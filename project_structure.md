# CLI Application Project Structure

```plaintext
my_tool/
├── bin/                # Compiled binaries or executable entry points
├── src/                # All source code
│   ├── my_tool/        # Main package
│   │   ├── cli/        # INTERFACE: Typer/Argparse/Click logic ONLY
│   │   │   ├── main.py # Entry point for the CLI
│   │   │   └── cmds/   # Subcommand definitions (download, sync, etc.)
│   │   │
│   │   ├── core/       # THE ENGINE: Pure logic, no CLI-specific code
│   │   │   ├── engine.py    # The "Brain" (orchestrating the tasks)
│   │   │   ├── models.py    # Data structures (Pydantic/Dataclasses)
│   │   │   └── exceptions.py# Custom errors (e.g., DownloadError)
│   │   │
│   │   ├── services/   # ADAPTERS: Talking to the outside world
│   │   │   ├── video.py     # yt-dlp / ffmpeg wrappers
│   │   │   ├── database.py  # Postgres/SQLAlchemy logic
│   │   │   └── filesystem.py# Pathlib/Low-level IO operations
│   │   │
│   │   └── utils/      # Helpers: Logging, Rich formatting, Banners
│   │
│   └── tests/          # Unit and Integration tests
├── config/             # Default config files (yaml/json)
├── pyproject.toml      # Build system & dependencies (the modern standard)
└── README.md
```
