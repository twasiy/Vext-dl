import shutil
from pathlib import Path
from typing import Any, Literal

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    computed_field,
    field_validator,
    model_serializer,
)

BASE_DIR = Path.home() / "Downloads"

ExtractFlatValue = bool | Literal["in_playlist", "discard", "discard_in_playlist"]

VideoContainer = Literal["mp4", "webm", "mkv"]
AudioCodec = Literal["mp3", "m4a", "wav", "flac", "opus"]
PlaylistContainer = Literal["mp4", "webm", "mkv", "mp3", "m4a", "opus", "flac", "wav"]

_AUDIO_CODECS: frozenset[str] = frozenset({"mp3", "m4a", "wav", "flac", "opus"})
_VIDEO_CONTAINERS: frozenset[str] = frozenset({"mp4", "webm", "mkv"})


def _parse_resolution(resolution: str) -> int:
    if not resolution or resolution == "best":
        return 0
    res_map = {
        "4k": 2160,
        "2k": 1440,
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
        "240p": 240,
        "144p": 144,
    }
    lower = resolution.lower()
    if lower in res_map:
        return res_map[lower]
    stripped = lower.rstrip("p")
    if stripped.isdigit():
        return int(stripped)
    digits = "".join(ch for ch in lower if ch.isdigit())
    return int(digits) if digits else 1080


def _build_video_format(resolution: str, container: str) -> str:
    if resolution == "best":
        return "bestvideo+bestaudio/best"

    height = _parse_resolution(resolution)

    if container == "webm":
        return (
            f"bestvideo[height<={height}][ext=webm]+bestaudio[ext=webm]/"
            f"bestvideo[height<={height}][ext=webm]+bestaudio/"
            f"bestvideo[height<={height}]+bestaudio/"
            "best"
        )
    elif container == "mkv":
        return (
            f"bestvideo[height<={height}]+bestaudio/"
            f"bestvideo[height<={height}]+bestaudio[ext=m4a]/"
            "best"
        )
    else:  # mp4
        return (
            f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={height}][ext=mp4]+bestaudio/"
            f"bestvideo[height<={height}]+bestaudio/"
            "best"
        )


def _build_embed_pps(
    embedmetadata: bool,
    embedthumbnail: bool,
    embedsubs: bool = False,
    video_mode: bool = False,
) -> list[dict[str, Any]]:
    pps: list[dict[str, Any]] = []
    if embedmetadata:
        pps.append({"key": "FFmpegMetadata", "add_chapters": True})
    if embedthumbnail:
        pps.append({"key": "EmbedThumbnail"})
    if embedsubs and video_mode:
        pps.append({"key": "FFmpegEmbedSubtitle"})
    return pps


def _coerce_paths(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {k: _coerce_paths(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_paths(item) for item in value]
    return value


def _sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for k, v in data.items():
        v = _coerce_paths(v)
        if v is None:
            continue
        if isinstance(v, list) and len(v) == 0:
            continue
        result[k] = v
    return result


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def get_best_js_runtimes():
    """
    Returns a dict of runtimes with their absolute paths if they exist.
    """
    # 1. Define common paths where these might live outside the standard PATH
    potential_paths = {
        "deno": [
            Path.home() / ".deno/bin/deno",
            "/usr/local/bin/deno",
            "/opt/homebrew/bin/deno",
        ],
        "node": [
            "/usr/bin/node",
            "/usr/local/bin/node",
            "/opt/homebrew/bin/node",
        ],
        "quickjs": [
            "/usr/bin/qjs",
            "/usr/local/bin/qjs",
            "/usr/bin/quickjs",
        ],
    }

    runtimes_config = {}

    for name, paths in potential_paths.items():
        # First, check if it's already in the system PATH
        system_path = shutil.which(name) or shutil.which(
            "qjs" if name == "quickjs" else name
        )

        if system_path:
            runtimes_config[name] = {"executable": system_path}
            continue

        # Second, check our list of "likely" absolute paths
        for path in paths:
            p = Path(path)
            if p.exists() and p.is_file():
                runtimes_config[name] = {"executable": str(p)}
                break

        # If still not found, include the key with an empty dict
        # so yt-dlp still tries to look for it itself.
        if name not in runtimes_config:
            runtimes_config[name] = {}

    return runtimes_config


class Base(BaseModel):
    model_config = {"populate_by_name": True}

    # --- Filesystem and Output ---
    outtmpl: str | dict[str, str] | None = Field(
        default="%(title)s.%(ext)s",
        description=(
            "Output filename template. String or dict keyed by OUTTMPL_TYPES. "
            "See yt-dlp OUTPUT TEMPLATE docs for format fields."
        ),
    )
    paths: dict[str, str] | None = Field(
        default_factory=lambda: {
            "home": str(BASE_DIR / "VEXT"),
            "temp": str(BASE_DIR / "VEXT" / ".temp"),
            "description": str(BASE_DIR / "VEXT" / ".metadata"),
            "subtitle": str(BASE_DIR / "VEXT" / ".metadata"),
        },
        description="Output path map. Keys: 'home', 'temp', and any OUTTMPL_TYPES key.",
    )
    download_archive: str | None = Field(
        default=None,
        description="Path to archive file. Videos whose IDs are in it are skipped.",
    )

    # --- Metadata Sidecar Files ---
    writethumbnail: bool = False
    writeautomaticsub: bool = False
    writesubtitles: bool = False
    writedescription: bool = False
    writeinfojson: bool = False

    # --- Post-processing / Embedding ---
    embedthumbnail: bool = False
    embedmetadata: bool = False
    embedsubs: bool = False

    # --- Network ---
    proxy: str | None = None
    cookiefile: str | None = Field(
        default=None,
        description="Path to Netscape-format cookies file.",
    )
    js_runtimes: dict[str, dict] = Field(
        default_factory=get_best_js_runtimes,
        description="JS runtimes config",
    )
    http_chunk_size: int | None = Field(
        default=None,
        description=(
            "HTTP chunk size in bytes for chunked downloads. "
            "None = yt-dlp default. Typical values: 10485760 (10 MB)."
        ),
    )

    # --- Retries ---
    retries: int = 10
    fragment_retries: int = 50
    file_access_retries: int = 3
    concurrent_fragment_downloads: int = Field(
        default=4,
        description="Parallel fragment threads for DASH/HLS. Keep ≤4 to avoid 429s.",
    )
    ratelimit: int | None = Field(
        default=None,
        description="Max download speed in bytes/sec. None = unlimited.",
    )

    buffersize: int = Field(
        default=1024 * 1024 * 16,
        description="Download buffer size in bytes. Default 16 MB.",
    )

    # --- Fragment Handling ---
    keepfragments: bool = False
    skip_unavailable_fragments: bool = True
    ignoreerrors: bool = False

    # --- Logging ---
    quiet: bool = False
    verbose: bool = False
    no_warnings: bool = Field(
        default=False,
        description="Suppress yt-dlp warnings in output.",
    )

    @model_serializer(mode="wrap")
    def _clean_for_ytdlp(self, handler: Any) -> dict[str, Any]:
        data = _sanitize_dict(handler(self))
        # no_warnings is read directly by Engine — not a yt-dlp option.
        data.pop("no_warnings", None)
        return data

    def to_ytdlp_dict(self) -> dict[str, Any]:
        return self.model_dump()


class VideoConfig(Base):
    resolution: str = Field(default="1080p", exclude=True)
    container: VideoContainer = Field(default="mp4", exclude=True)
    noplaylist: bool = True

    @field_validator("resolution", mode="before")
    @classmethod
    def _coerce_resolution(cls, v: Any) -> str:
        return v if v is not None else "1080p"

    @field_validator("container", mode="before")
    @classmethod
    def _coerce_container(cls, v: Any) -> str:
        return v if v is not None else "mp4"

    @computed_field
    @property
    def format(self) -> str:
        return _build_video_format(self.resolution, self.container)

    @computed_field
    @property
    def merge_output_format(self) -> str:
        return self.container

    @computed_field
    @property
    def postprocessors(self) -> list[dict[str, Any]]:
        return _build_embed_pps(
            self.embedmetadata,
            self.embedthumbnail,
            self.embedsubs,
            video_mode=True,
        )


class AudioConfig(Base):
    audio_format: AudioCodec = Field(default="mp3", exclude=True)
    audio_quality: int = Field(
        default=192,
        exclude=True,
        description="Bitrate in kbps. Lossy formats only (mp3, m4a, opus).",
    )
    noplaylist: bool = True
    embedthumbnail: bool = True

    @field_validator("audio_format", mode="before")
    @classmethod
    def _coerce_audio_format(cls, v: Any) -> str:
        return v if v is not None else "mp3"

    @field_validator("audio_quality", mode="before")
    @classmethod
    def _coerce_audio_quality(cls, v: Any) -> int:
        return v if v is not None else 192

    @computed_field
    @property
    def format(self) -> str:
        return "bestaudio/best"

    @computed_field
    @property
    def postprocessors(self) -> list[dict[str, Any]]:
        pps: list[dict[str, Any]] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.audio_format,
                "preferredquality": str(self.audio_quality),
            }
        ]
        pps.extend(_build_embed_pps(self.embedmetadata, self.embedthumbnail))
        return pps


class PlaylistConfig(Base):
    mode: Literal["video", "audio"] = Field(default="video", exclude=True)
    resolution: str = Field(default="720p", exclude=True)
    container: PlaylistContainer = Field(default="mp4", exclude=True)
    audio_quality: int = Field(
        default=192,
        exclude=True,
        description="Bitrate in kbps. Used in audio mode only.",
    )

    _extract_flat: ExtractFlatValue = PrivateAttr(default=False)

    def __init__(self, *, extract_flat: ExtractFlatValue = False, **data: Any) -> None:
        super().__init__(**data)
        self._extract_flat = extract_flat

    playlist_items: str | None = Field(
        None,
        description=(
            "Playlist indices to download. "
            "Supports slices and steps: '1,2,5-10', '5:10', '1::2'. "
            "None = download all."
        ),
    )
    noplaylist: bool = False
    lazy_playlist: bool = True

    @field_validator("resolution", mode="before")
    @classmethod
    def _coerce_resolution(cls, v: Any) -> str:
        return v if v is not None else "720p"

    @field_validator("container", mode="before")
    @classmethod
    def _coerce_container(cls, v: Any) -> str:
        return v if v is not None else "mp4"

    @field_validator("audio_quality", mode="before")
    @classmethod
    def _coerce_audio_quality(cls, v: Any) -> int:
        return v if v is not None else 192

    @computed_field
    @property
    def format(self) -> str:
        if self.mode == "audio":
            return "bestaudio/best"
        effective_container = (
            self.container if self.container in _VIDEO_CONTAINERS else "mp4"
        )
        return _build_video_format(self.resolution, effective_container)

    @computed_field
    @property
    def postprocessors(self) -> list[dict[str, Any]]:
        pps: list[dict[str, Any]] = []

        if self.mode == "audio":
            audio_codec: str = (
                self.container if self.container in _AUDIO_CODECS else "mp3"
            )
            pps.append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_codec,
                    "preferredquality": str(self.audio_quality),
                }
            )

        pps.extend(
            _build_embed_pps(
                self.embedmetadata,
                self.embedthumbnail,
                self.embedsubs,
                video_mode=(self.mode == "video"),
            )
        )
        return pps

    @computed_field
    @property
    def merge_output_format(self) -> str | None:
        if self.mode == "video" and self.container in _VIDEO_CONTAINERS:
            return self.container
        return None

    @model_serializer(mode="wrap")
    def _clean_for_ytdlp(self, handler: Any) -> dict[str, Any]:
        data = _sanitize_dict(handler(self))
        data["extract_flat"] = self._extract_flat
        data.pop("no_warnings", None)
        return data
