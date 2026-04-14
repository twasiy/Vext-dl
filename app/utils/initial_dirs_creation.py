from pathlib import Path

BASE_DIR = Path.home() / "Downloads" / "VEXT"


def create_initial_dirs() -> None:
    config_file = Path.home() / ".vext.json"

    if not config_file.exists():
        config_file.touch()

    subdirs = ["Audios", "Videos", "Playlists", ".temp", ".metadata"]

    for subdir in subdirs:
        target_path = BASE_DIR / subdir
        target_path.mkdir(parents=True, exist_ok=True)
