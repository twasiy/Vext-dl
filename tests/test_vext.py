"""
Vext-dl Test Suite
==================
Minimal yet effective tests focused on pure logic — no network, no yt-dlp calls.
Covers: config logic, settings I/O, DownloadResult, and CLI helper functions.
"""

import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path setup — point to app/ so imports work without installing the package
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

"""All of these imports below will be loaded in runtime. so let IDEs to mark Squiggle lines"""

from cli.single_video_cmd import _fmt_bytes, _fmt_seconds
from core.config import (
    AudioConfig,
    PlaylistConfig,
    VideoConfig,
    _build_embed_pps,
    _build_video_format,
    _parse_resolution,
)
from core.engine import DownloadResult
from core.settings import Settings

# ===========================================================================
# 1. Resolution Parsing  (config._parse_resolution)
# ===========================================================================


class TestParseResolution:
    def test_named_labels(self):
        assert _parse_resolution("1080p") == 1080
        assert _parse_resolution("720p") == 720
        assert _parse_resolution("4k") == 2160
        assert _parse_resolution("2k") == 1440

    def test_numeric_with_p(self):
        assert _parse_resolution("480p") == 480
        assert _parse_resolution("360p") == 360

    def test_best_returns_zero(self):
        assert _parse_resolution("best") == 0

    def test_empty_returns_zero(self):
        assert _parse_resolution("") == 0

    def test_raw_digits(self):
        # "1080" without 'p' — falls through to digit extraction
        assert _parse_resolution("1080") == 1080


# ===========================================================================
# 2. Video Format String  (config._build_video_format)
# ===========================================================================


class TestBuildVideoFormat:
    def test_best_resolution(self):
        fmt = _build_video_format("best", "mp4")
        assert fmt == "bestvideo+bestaudio/best"

    def test_mp4_contains_height(self):
        fmt = _build_video_format("1080p", "mp4")
        assert "1080" in fmt
        assert "mp4" in fmt

    def test_webm_uses_webm_ext(self):
        fmt = _build_video_format("720p", "webm")
        assert "720" in fmt
        assert "webm" in fmt

    def test_mkv_no_ext_filter(self):
        # mkv format should NOT filter by ext=mp4/webm
        fmt = _build_video_format("1080p", "mkv")
        assert "ext=mp4" not in fmt
        assert "1080" in fmt

    def test_fallback_to_best(self):
        # Every format string must end with a /best fallback
        for res in ("720p", "1080p", "4k"):
            for container in ("mp4", "webm", "mkv"):
                assert _build_video_format(res, container).endswith(
                    "/best"
                ) or "best" in _build_video_format(res, container)


# ===========================================================================
# 3. Embed Post-processors  (config._build_embed_pps)
# ===========================================================================


class TestBuildEmbedPps:
    def test_empty_when_all_false(self):
        assert _build_embed_pps(False, False, False) == []

    def test_metadata_pp_added(self):
        pps = _build_embed_pps(True, False)
        keys = [p["key"] for p in pps]
        assert "FFmpegMetadata" in keys

    def test_thumbnail_pp_added(self):
        pps = _build_embed_pps(False, True)
        keys = [p["key"] for p in pps]
        assert "EmbedThumbnail" in keys

    def test_subs_only_in_video_mode(self):
        pps_video = _build_embed_pps(False, False, embedsubs=True, video_mode=True)
        pps_audio = _build_embed_pps(False, False, embedsubs=True, video_mode=False)
        assert any(p["key"] == "FFmpegEmbedSubtitle" for p in pps_video)
        assert not any(p["key"] == "FFmpegEmbedSubtitle" for p in pps_audio)

    def test_all_enabled_video_mode(self):
        pps = _build_embed_pps(True, True, embedsubs=True, video_mode=True)
        keys = [p["key"] for p in pps]
        assert "FFmpegMetadata" in keys
        assert "EmbedThumbnail" in keys
        assert "FFmpegEmbedSubtitle" in keys


# ===========================================================================
# 4. Config Models  (VideoConfig, AudioConfig, PlaylistConfig)
# ===========================================================================


class TestVideoConfig:
    def test_default_format_contains_1080(self):
        cfg = VideoConfig()
        assert "1080" in cfg.format

    def test_custom_resolution(self):
        cfg = VideoConfig(resolution="720p")
        assert "720" in cfg.format

    def test_merge_output_format_matches_container(self):
        cfg = VideoConfig(container="mkv")
        assert cfg.merge_output_format == "mkv"

    def test_none_resolution_coerced_to_default(self):
        cfg = VideoConfig(resolution=None)
        assert cfg.resolution == "1080p"

    def test_to_ytdlp_dict_has_format(self):
        d = VideoConfig().to_ytdlp_dict()
        assert "format" in d


class TestAudioConfig:
    def test_default_format_is_bestaudio(self):
        cfg = AudioConfig()
        assert cfg.format == "bestaudio/best"

    def test_postprocessors_contains_extract_audio(self):
        cfg = AudioConfig(audio_format="mp3", audio_quality=192)
        keys = [p["key"] for p in cfg.postprocessors]
        assert "FFmpegExtractAudio" in keys

    def test_audio_quality_in_postprocessor(self):
        cfg = AudioConfig(audio_quality=320)
        extract_pp = next(
            p for p in cfg.postprocessors if p["key"] == "FFmpegExtractAudio"
        )
        assert extract_pp["preferredquality"] == "320"

    def test_none_audio_format_coerced(self):
        cfg = AudioConfig(audio_format=None)
        assert cfg.audio_format == "mp3"


class TestPlaylistConfig:
    def test_video_mode_default(self):
        cfg = PlaylistConfig()
        assert cfg.mode == "video"
        assert "720" in cfg.format  # default resolution

    def test_audio_mode_format(self):
        cfg = PlaylistConfig(mode="audio")
        assert cfg.format == "bestaudio/best"

    def test_audio_mode_postprocessors_has_extract(self):
        cfg = PlaylistConfig(mode="audio")
        keys = [p["key"] for p in cfg.postprocessors]
        assert "FFmpegExtractAudio" in keys

    def test_video_mode_merge_output_format(self):
        cfg = PlaylistConfig(mode="video", container="mkv")
        assert cfg.merge_output_format == "mkv"

    def test_audio_mode_merge_output_is_none(self):
        cfg = PlaylistConfig(mode="audio")
        assert cfg.merge_output_format is None

    def test_extract_flat_in_serialized_dict(self):
        cfg = PlaylistConfig(extract_flat="in_playlist")
        d = cfg.to_ytdlp_dict()
        assert d["extract_flat"] == "in_playlist"

    def test_noplaylist_false_for_playlists(self):
        cfg = PlaylistConfig()
        assert cfg.noplaylist is False


# ===========================================================================
# 5. Settings  (core.settings.Settings)
# ===========================================================================


class TestSettings:
    @pytest.fixture(autouse=True)
    def isolate_config(self, tmp_path, monkeypatch):
        """Redirect config file to a temp dir so we never touch ~/.vext.json"""
        fake_path = tmp_path / ".vext.json"
        monkeypatch.setattr(Settings, "CONFIG_PATH", fake_path)

    def test_load_returns_defaults_when_no_file(self):
        s = Settings.load()
        assert s["res"] == "1080p"
        assert s["ext_video"] == "mp4"
        assert s["threads"] == 4

    def test_save_and_load_roundtrip(self):
        Settings.save("res", "720p")
        s = Settings.load()
        assert s["res"] == "720p"

    def test_save_integer_value(self):
        Settings.save("threads", 8)
        s = Settings.load()
        assert s["threads"] == 8

    def test_save_none_value(self):
        Settings.save("proxy", None)
        s = Settings.load()
        assert s["proxy"] is None

    def test_clear_removes_file(self):
        Settings.save("res", "4k")
        Settings.clear()
        assert not Settings.CONFIG_PATH.exists()

    def test_load_after_clear_returns_defaults(self):
        Settings.save("res", "4k")
        Settings.clear()
        s = Settings.load()
        assert s["res"] == "1080p"

    def test_corrupt_json_falls_back_to_defaults(self):
        Settings.CONFIG_PATH.write_text("not valid json{{{{")
        s = Settings.load()
        assert s["res"] == "1080p"

    def test_unknown_keys_not_loaded(self):
        Settings.CONFIG_PATH.write_text(json.dumps({"totally_fake_key": "value"}))
        s = Settings.load()
        assert "totally_fake_key" not in s

    def test_get_allowed_keys_matches_defaults(self):
        assert set(Settings.get_allowed_keys()) == set(Settings.DEFAULTS.keys())


# ===========================================================================
# 6. DownloadResult  (core.engine.DownloadResult)
# ===========================================================================


class TestDownloadResult:
    def test_success_is_truthy(self):
        r = DownloadResult(success=True, filename="video.mp4")
        assert bool(r) is True

    def test_failure_is_falsy(self):
        r = DownloadResult(success=False, error="Network error")
        assert bool(r) is False

    def test_repr_ok(self):
        r = DownloadResult(success=True, filename="song.mp3")
        assert "OK" in repr(r)
        assert "song.mp3" in repr(r)

    def test_repr_failed(self):
        r = DownloadResult(success=False, error="timeout")
        assert "FAILED" in repr(r)
        assert "timeout" in repr(r)


# ===========================================================================
# 7. CLI Helper Functions  (_fmt_seconds, _fmt_bytes)
# ===========================================================================


class TestFmtSeconds:
    def test_none_returns_na(self):
        assert _fmt_seconds(None) == "N/A"

    def test_under_one_hour(self):
        assert _fmt_seconds(90) == "1:30"
        assert _fmt_seconds(3599) == "59:59"

    def test_over_one_hour(self):
        assert _fmt_seconds(3661) == "1:01:01"

    def test_zero(self):
        assert _fmt_seconds(0) == "0:00"

    def test_float_input(self):
        assert _fmt_seconds(90.9) == "1:30"  # truncates to int


class TestFmtBytes:
    def test_bytes(self):
        assert _fmt_bytes(512) == "512.0 B"

    def test_kilobytes(self):
        assert _fmt_bytes(2048) == "2.0 KB"

    def test_megabytes(self):
        assert _fmt_bytes(1024 * 1024 * 5) == "5.0 MB"

    def test_gigabytes(self):
        assert _fmt_bytes(1024**3 * 2) == "2.0 GB"

    def test_terabytes(self):
        assert _fmt_bytes(1024**4 * 3) == "3.0 TB"
