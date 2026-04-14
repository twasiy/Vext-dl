import json
from pathlib import Path
from typing import Any


class Settings:
    CONFIG_PATH = Path.home() / ".vext.json"

    # Factory Defaults
    DEFAULTS = {
        "res": "1080p",
        "ext_video": "mp4",
        "ext_audio": "mp3",
        "bitrate": 192,
        "threads": 4,
        "output_path": None,
        "proxy": None,
        "cookie": None,
        "archive": None,
        "limit": None,
    }

    # Documentation for the user
    DESCRIPTIONS = {
        "res": "Maximum video resolution (e.g., 1080p, 720p, 4k).",
        "ext_video": "Default video container (mp4, webm, mkv).",
        "ext_audio": "Default audio format (mp3, m4a, wav, flac, opus).",
        "bitrate": "Audio quality bitrate in kbps (128, 192, 320).",
        "threads": "Number of concurrent download fragments (1-16).",
        "output_path": "Global base directory for all downloads.",
        "proxy": "Proxy URL for network requests.",
        "cookie": "Cookie file path for user-specific / restricted content.",
        "archive": "Archive file path for tracking downloaded IDs.",
        "limit": "Download speed limit in bytes per second (None = unlimited).",
    }

    @classmethod
    def get_allowed_keys(cls):
        return list(cls.DEFAULTS.keys())

    @classmethod
    def load(cls) -> dict[str, Any]:
        """Loads settings from JSON and merges them with defaults."""
        settings = cls.DEFAULTS.copy()
        if cls.CONFIG_PATH.exists():
            try:
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    valid_data = {
                        k: v for k, v in user_data.items() if k in cls.DEFAULTS
                    }
                    settings.update(valid_data)
            except Exception:
                pass  # Fallback to defaults if JSON is corrupt
        return settings

    @classmethod
    def save(cls, key: str, value: Any) -> None:
        """Updates a single setting in the JSON file."""
        data: dict[str, Any] = {}
        if cls.CONFIG_PATH.exists():
            try:
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        data[key] = value
        with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def clear(cls) -> None:
        cls.CONFIG_PATH.unlink(missing_ok=True)
