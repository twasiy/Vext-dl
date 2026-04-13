import logging
from typing import Any, Callable

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from yt_dlp import YoutubeDL

from .config import Base

ProgressCallback = Callable[[str, str, str], None]  # percent, speed, eta


class DownloadResult:
    def __init__(
        self, success: bool, filename: str | None = None, error: str | None = None
    ):
        self.success = success
        self.filename = filename
        self.error = error

    def __bool__(self) -> bool:
        return self.success

    def __repr__(self) -> str:
        if self.success:
            return f"<DownloadResult OK: {self.filename}>"
        return f"<DownloadResult FAILED: {self.error}>"


class Engine:
    def __init__(self, config: Base, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("Vext")
        self._config = config

        self.opts = config.to_ytdlp_dict()
        self.opts.update(
            {
                "logger": self.logger,
                "quiet": True,
                "no_warnings": config.no_warnings,
            }
        )

        self.ydl = YoutubeDL(self.opts)  # type:ignore
        self.ydl.__enter__()
        self._entered = True

    # --- Context-manager support ---

    def __enter__(self) -> "Engine":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        if getattr(self, "_entered", False):
            try:
                self.ydl.__exit__(None, None, None)
            except Exception:
                pass
            self._entered = False

    # --- Internal helpers ---

    def _get_progress_hook(self, progress: Progress, task_id: Any) -> Callable:
        def hook(d: dict[str, Any]) -> None:
            if d["status"] == "downloading":
                completed = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                if total:
                    progress.update(task_id, completed=completed, total=total)

            elif d["status"] == "finished":
                total_bytes = d.get("total_bytes") or d.get("downloaded_bytes", 0)
                if total_bytes:
                    progress.update(task_id, completed=total_bytes, total=total_bytes)

        return hook

    # --- Public API ---

    def download(self, url: str) -> bool:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.0f}%",
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task(description="Initializing...", total=None)

            self.ydl.params["progress_hooks"] = [
                self._get_progress_hook(progress, task_id)
            ]

            # self.ydl._progress_hooks.clear()
            self.ydl.params["progress_hooks"].clear()
            self.ydl.add_progress_hook(self._get_progress_hook(progress, task_id))

            try:
                info = self.ydl.extract_info(url, download=False)
                if info:
                    title = info.get("title", "Video")
                    progress.update(task_id, description=f"Working: {title[:40]}...")  # type:ignore
                return self.ydl.download([url]) == 0
            except Exception as e:
                self.logger.error(f"Download failed: {e}")
                return False

    def get_info(self, url: str) -> dict[str, Any] | None:
        info_opts = {**self.opts}
        if not info_opts.get("extract_flat"):
            info_opts["extract_flat"] = "in_playlist"
        info_opts["skip_download"] = True

        try:
            with YoutubeDL(info_opts) as ydl:  # type:ignore
                return ydl.sanitize_info(ydl.extract_info(url, download=False))  # type:ignore
        except Exception:
            return None
