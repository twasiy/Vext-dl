<div align="center">

# ⚡ Vext-dl

**A high-performance, production-ready CLI media downloader.**  
Download videos, audio, and playlists from YouTube and 1000+ sites — with rich progress, smart defaults, and persistent config.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![yt-dlp](https://img.shields.io/badge/Powered%20by-yt--dlp-red)](https://github.com/yt-dlp/yt-dlp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Video](#video-commands)
  - [Audio](#audio-commands)
  - [Playlist](#playlist-commands)
  - [Archive](#archive-commands)
  - [Config](#config-commands)
  - [Command Map](#command-map)
- [Configuration](#-configuration)
- [Output Structure](#-output-structure)
- [Advanced Usage](#-advanced-usage)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔍 Overview

**Vext-dl** is a feature-rich, terminal-based media downloader built on top of [`yt-dlp`](https://github.com/yt-dlp/yt-dlp). It wraps yt-dlp's powerful engine with a clean, opinionated CLI using [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich) — giving you a beautiful, fast, and scriptable download workflow.

Whether you need a single video, a batch of audio tracks, or an entire playlist — Vext handles it with live progress bars, smart format selection, persistent settings, and download archive tracking.

---

## ✨ Features

- 🎬 **Video Downloads** — Resolution-aware format selection (144p → 4K), multi-container support (`mp4`, `mkv`, `webm`)
- 🎵 **Audio Extraction** — High-quality audio with codec selection (`mp3`, `flac`, `opus`, `wav`, `m4a`) and bitrate control
- 📂 **Playlist Batch Downloads** — Full playlist support with item filtering (`1-5`, `1::2`), smart subfolder organization
- 📊 **Rich Media Info** — Inspect video/audio/playlist metadata, formats, subtitles, and chapters — without downloading
- 📦 **Archive Tracking** — Track downloaded IDs to prevent re-downloads across sessions
- ⚙️ **Persistent Config** — Save global defaults (resolution, format, threads, proxy, etc.) to `~/.vext.json`
- 🌐 **Proxy & Cookie Support** — Full proxy and Netscape-format cookie file support for restricted content
- 🚀 **Concurrent Fragment Downloads** — Multi-threaded DASH/HLS fragment downloading
- 🎨 **Beautiful Terminal UI** — Live progress bars, Rich tables, colored panels via [Rich](https://github.com/Textualize/rich)
- 🔁 **Batch URL Files** — Pass `--file urls.txt` to download multiple URLs in one command
- 🏷️ **Metadata & Thumbnail Embedding** — Auto-embed title, artist, chapters, thumbnails, and subtitles into files

---

## 🗂️ Project Structure

```
Vext-dl/
├── main.py                         # Project root entry point
└── app/
    ├── main.py                     # Typer app: registers all sub-apps
    ├── cli/
    │   ├── __init__.py
    │   ├── single_video_cmd.py     # `video get` / `video info`
    │   ├── single_audio_cmd.py     # `audio get` / `audio info`
    │   ├── playlist_cmd.py         # `playlist get` / `playlist info`
    │   ├── archive_cmd.py          # `archive show/add/clear`
    │   └── config_cmd.py           # `config show/set`
    ├── core/
    │   ├── __init__.py
    │   ├── config.py               # Pydantic models: VideoConfig, AudioConfig, PlaylistConfig
    │   ├── engine.py               # yt-dlp wrapper with Rich progress hooks
    │   └── settings.py             # Persistent JSON settings manager
    └── utils/
        ├── __init__.py
        └── initial_dirs_creation.py  # Creates ~/Downloads/VEXT/ subdirectories
```

---

## 📋 Requirements

- **Python** 3.11+
- **FFmpeg** — Required for post-processing (metadata embedding, audio extraction, subtitle embedding, thumbnail embedding)
- **Node.js / Deno / QuickJS** _(optional)_ — For JS-based extractor support in yt-dlp

Install FFmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Fedora / Redhat
sudo dnf5 install ffmpeg

# Windows (via Chocolatey)
choco install ffmpeg
```

---

## 🚀 Installation

**1. Clone the repository:**

```bash
git clone https://github.com/twasiy/Vext-dl
cd Vext-dl
```

**2. Set up the environment (Recommended)**

The fastest way to get started is using **uv**. This automatically creates a virtual environment and installs all dependencies from `pyproject.toml` in one go:

```bash
uv sync
```

**3. Manual setup (Alternative):**

- Create and Activate the enviroment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows .venv\Scripts\activate
```

- Install Dependencies:

```bash
pip install yt-dlp typer rich pydantic
```

**4. Run the CLI:**

```bash
cd app
uv run main.py --help  # (Recommended)
python main.py --help  # (Alternative)

```

---

## 🛠️ Usage

All commands follow this structure:

```
uv run main.py [ENGINE] [SUBCOMMAND] [ARGUMENTS] [OPTIONS]  # (Recommended)
python main.py [ENGINE] [SUBCOMMAND] [ARGUMENTS] [OPTIONS]  # (Alternative)
```

---

### Video Commands

#### Download a video

```bash
uv run main.py video get <URL>
```

```bash
# Download in 1080p MP4
uv run main.py video get "https://youtube.com/watch?v=..." --res 1080p --ext mp4

# Download with embedded subtitles and thumbnail
uv run main.py video get "https://youtube.com/watch?v=..." --subs --thumb --meta

# Download multiple URLs from a file
uv run main.py video get --file urls.txt --res 720p

# Use a proxy and cookie file
uv run main.py video get "https://..." --proxy http://user:pass@host:port --cookie cookies.txt

# Limit download speed to 2 MB/s
uv run main.py video get "https://..." --limit 2097152

# Use archive to skip already-downloaded videos
uv run main.py video get "https://..." --archive archive.txt
```

**Available options:**

| Option              | Description                                                                    |
| ------------------- | ------------------------------------------------------------------------------ |
| `--res`             | Max resolution: `144p`, `360p`, `480p`, `720p`, `1080p`, `2160p`, `4k`, `best` |
| `--ext`             | Container: `mp4`, `webm`, `mkv`                                                |
| `--threads`, `-t`   | Concurrent fragment download threads                                           |
| `--path`, `-p`      | Custom output directory                                                        |
| `--subs`            | Embed available subtitle tracks                                                |
| `--write-subs`      | Save subtitles as sidecar files                                                |
| `--write-auto-subs` | Save auto-generated captions                                                   |
| `--thumb`           | Embed thumbnail into file                                                      |
| `--write-thumb`     | Save thumbnail as separate image                                               |
| `--meta`, `-m`      | Embed metadata (title, uploader, chapters)                                     |
| `--write-desc`      | Save description as sidecar file                                               |
| `--proxy`           | Proxy URL                                                                      |
| `--cookie`          | Path to Netscape cookies file                                                  |
| `--limit`           | Download speed limit in bytes/sec                                              |
| `--archive`, `-a`   | Path to archive file (skip already-downloaded)                                 |
| `--file`, `-f`      | Text file with one URL per line                                                |
| `--verbose`, `-v`   | Show raw yt-dlp logs                                                           |

#### Inspect a video (no download)

```bash
uv run main.py video info "https://youtube.com/watch?v=..."

# Show all available formats and resolutions
uv run main.py video info "https://..." --fetch-formats

# Show available subtitle languages
uv run main.py video info "https://..." --fetch-subs
```

---

### Audio Commands

#### Download audio

```bash
uv run main.py audio get <URL>
```

```bash
# Download as MP3 at 320kbps
uv run main.py audio get "https://youtube.com/watch?v=..." --ext mp3 --bitrate 320

# Download as FLAC (lossless)
uv run main.py audio get "https://youtube.com/watch?v=..." --ext flac

# Batch download from file, embed metadata and thumbnail
uv run main.py audio get --file songs.txt --meta --thumb

# Save info JSON and thumbnail as sidecar files
uv run main.py audio get "https://..." --write-json --write-thumb
```

**Available options:**

| Option                     | Description                                      |
| -------------------------- | ------------------------------------------------ |
| `--ext`                    | Audio codec: `mp3`, `m4a`, `wav`, `flac`, `opus` |
| `--bitrate`                | Quality in kbps: `128`, `192`, `256`, `320`      |
| `--thumb / --no-thumb`     | Embed thumbnail as album art (default: on)       |
| `--meta / --no-meta`, `-m` | Embed metadata (default: on)                     |
| `--write-thumb`            | Save thumbnail as separate file                  |
| `--write-desc`             | Save description as sidecar file                 |
| `--write-json`             | Save metadata as `.info.json`                    |
| `--threads`, `-t`          | Concurrent fragment threads                      |
| `--path`, `-p`             | Custom output directory                          |
| `--proxy`                  | Proxy URL                                        |
| `--cookie`                 | Path to cookies file                             |
| `--limit`                  | Speed limit in bytes/sec                         |
| `--archive`, `-a`          | Archive file to avoid re-downloads               |
| `--file`, `-f`             | Text file with one URL per line                  |
| `--verbose`, `-v`          | Verbose output                                   |

#### Inspect audio (no download)

```bash
uv run main.py audio info "https://youtube.com/watch?v=..."

# Show extended artist/album/genre metadata
uv run main.py audio info "https://..." --fetch-meta

# Show thumbnail URL
uv run main.py audio info "https://..." --fetch-thumb
```

---

### Playlist Commands

#### Download a playlist

```bash
uv run main.py playlist get <PLAYLIST_URL>
```

```bash
# Download entire playlist as video
uv run main.py playlist get "https://youtube.com/playlist?list=..."

# Download as audio (MP3)
uv run main.py playlist get "https://..." --mode audio --ext mp3

# Download only items 1-10
uv run main.py playlist get "https://..." --items "1-10"

# Download every other video (1, 3, 5...)
uv run main.py playlist get "https://..." --items "1::2"

# Custom output folder
uv run main.py playlist get "https://..." --path ~/Music/MyPlaylist
```

**Available options:**

| Option            | Description                                         |
| ----------------- | --------------------------------------------------- |
| `--mode`          | `video` (default) or `audio`                        |
| `--res`           | Max resolution for video mode                       |
| `--ext`           | Container/codec (`mp4`, `mkv`, `mp3`, `flac`, etc.) |
| `--bitrate`       | Audio bitrate (audio mode)                          |
| `--items`, `-i`   | Item selector: `1,2,5-10` or `start:end:step`       |
| `--threads`, `-t` | Concurrent fragment threads                         |
| `--path`, `-p`    | Custom base output directory                        |
| `--thumb`         | Embed thumbnails as cover art                       |
| `--write-thumb`   | Save thumbnails as sidecar files                    |
| `--meta`, `-m`    | Embed metadata                                      |
| `--subs`          | Embed subtitles (video mode only)                   |
| `--write-desc`    | Save descriptions                                   |
| `--write-json`    | Save `.info.json` for each item                     |
| `--proxy`         | Proxy URL                                           |
| `--cookie`        | Path to cookies file                                |
| `--limit`         | Global speed limit (bytes/sec)                      |
| `--archive`, `-a` | Archive file to skip duplicates                     |
| `--file`, `-f`    | Text file with playlist URLs                        |
| `--verbose`, `-v` | Verbose output                                      |

#### Inspect a playlist (no download)

```bash
uv run main.py playlist info "https://youtube.com/playlist?list=..."

# Inspect only the first 5 items
uv run main.py playlist info "https://..." --items "1-5"
```

---

### Archive Commands

The archive system uses yt-dlp's native archive format (`{extractor} {id}`) to track downloads and skip duplicates.

```bash
# View the last 10 entries in an archive
uv run main.py archive show archive.txt

# Manually add a video ID to the archive (to mark it as already downloaded)
uv run main.py archive add archive.txt --id "dQw4w9WgXcQ" --site youtube

# Clear the archive to allow re-downloading everything
uv run main.py archive clear archive.txt
```

---

### Config Commands

Manage global persistent defaults, stored in `~/.vext.json`.

```bash
# View all settings and their current values
uv run main.py config show

# Set a default value
uv run main.py config set res 1080p
uv run main.py config set ext_video mkv
uv run main.py config set ext_audio flac
uv run main.py config set bitrate 320
uv run main.py config set threads 8
uv run main.py config set output_path /home/user/Media
uv run main.py config set proxy http://127.0.0.1:8080
uv run main.py config set limit 5242880   # 5 MB/s

# Reset a value to "None" (use default behavior)
uv run main.py config set proxy none

# Clear the cofig file
uv run main.py config clear
```

**All configurable keys:**

| Key           | Default | Description                   |
| ------------- | ------- | ----------------------------- |
| `res`         | `1080p` | Maximum video resolution      |
| `ext_video`   | `mp4`   | Default video container       |
| `ext_audio`   | `mp3`   | Default audio codec           |
| `bitrate`     | `192`   | Audio quality in kbps         |
| `threads`     | `4`     | Concurrent download fragments |
| `output_path` | `None`  | Global base output directory  |
| `proxy`       | `None`  | Proxy URL                     |
| `cookie`      | `None`  | Path to cookies file          |
| `archive`     | `None`  | Default archive file path     |
| `limit`       | `None`  | Speed limit in bytes/sec      |

---

### Command Map

View all available commands at a glance:

```bash
uv run main.py map
```

---

## ⚙️ Configuration

Settings are persisted to `~/.vext.json` and automatically loaded on every run. CLI flags always override saved settings.

Example `~/.vext.json`:

```json
{
  "res": "1080p",
  "ext_video": "mp4",
  "ext_audio": "mp3",
  "bitrate": 192,
  "threads": 4,
  "output_path": null,
  "proxy": null,
  "cookie": null,
  "archive": null,
  "limit": null
}
```

---

## 📁 Output Structure

By default, Vext saves files to `~/Downloads/VEXT/`:

```
~/Downloads/VEXT/
├── Videos/
│   └── Video Title.mp4
├── Audios/
│   └── Song Title.mp3
├── Playlists/
│   └── Playlist Name/
│       ├── Video 1.mp4
│       └── Video 2.mp4
├── .temp/          # Temporary fragment files (auto-cleaned)
└── .metadata/      # Sidecar files: .description, .srt, etc.
```

---

## 🔬 Advanced Usage

#### Download with cookies for age-restricted content

Export your browser cookies using a tool like [cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/) and pass them:

```bash
uv run main.py video get "https://..." --cookie ~/cookies.txt
```

#### Batch download from a URL file

```bash
# urls.txt
https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
https://youtu.be/ghi789

uv run main.py audio get --file urls.txt --ext flac
```

#### Set a global archive to never re-download

```bash
uv run main.py config set archive ~/.vext_archive.txt

# All future downloads will automatically check and update this archive
uv run main.py video get "https://..."
```

#### Download a playlist, audio mode, lossless

```bash
uv run main.py playlist get "https://youtube.com/playlist?list=..." \
    --mode audio \
    --ext flac \
    --meta \
    --archive ~/.vext_archive.txt \
    --threads 8
```

---

## 🤝 Contributing

Contributions are welcome! To get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and write clear commit messages
4. Push to your fork and open a Pull Request

Please make sure your code passes linting and follows the existing style.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

<div align="center">

Built with ❤️ by Tassok using [yt-dlp](https://github.com/yt-dlp/yt-dlp), [Typer](https://typer.tiangolo.com/), and [Rich](https://github.com/Textualize/rich)

</div>
