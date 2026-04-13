from pathlib import Path
from typing import Annotated

import typer
from core import BASE_DIR, AudioCodec, AudioConfig, Engine, Settings
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

audio_app = typer.Typer(help="Extract and download audio files.")


@audio_app.command("get")
def download_audio(
    url: Annotated[
        str | None,
        typer.Argument(help="The URL to download. Optional if --file is used."),
    ] = None,
    input_file: Annotated[
        str | None,
        typer.Option(
            "--file", "-f", help="Path to a text file containing URLs (one per line)."
        ),
    ] = None,
    ext: Annotated[
        AudioCodec | None,
        typer.Option("--ext", help="Target audio format (e.g., mp3, flac, opus)."),
    ] = None,
    bitrate: Annotated[
        int | None,
        typer.Option("--bitrate", help="Audio quality bitrate (e.g., 128, 192, 320)."),
    ] = None,
    output_path: Annotated[
        str | None,
        typer.Option(
            "--path", "-p", help="Custom directory path for the saved audio file."
        ),
    ] = None,
    threads: Annotated[
        int | None,
        typer.Option("--threads", "-t", help="Number of concurrent download threads."),
    ] = None,
    write_thumb: Annotated[
        bool,
        typer.Option(
            "--write-thumb", help="Save the thumbnail as a separate image file."
        ),
    ] = False,
    write_desc: Annotated[
        bool,
        typer.Option(
            "--write-desc", help="Save the video description to a .description file."
        ),
    ] = False,
    write_json: Annotated[
        bool,
        typer.Option(
            "--write-json", help="Save the full metadata to a .info.json file."
        ),
    ] = False,
    thumb: Annotated[
        bool,
        typer.Option(
            "--thumb/--no-thumb", help="Embed the video thumbnail as album art."
        ),
    ] = True,
    meta: Annotated[
        bool,
        typer.Option(
            "--meta/--no-meta",
            "-m",
            help="Embed metadata such as Artist, Title, and Year.",
        ),
    ] = True,
    proxy: Annotated[
        str | None,
        typer.Option("--proxy", help="Use a proxy (e.g., http://user:pass@host:port)."),
    ] = None,
    cookie: Annotated[
        str | None,
        typer.Option(
            "--cookie",
            help="Path to a cookies.txt file for access to restricted content.",
        ),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", help="Download speed limit in bytes per second."),
    ] = None,
    archive: Annotated[
        str | None,
        typer.Option(
            "--archive", "-a", help="Path to archive file to track and skip duplicates."
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable detailed debug logging.")
    ] = False,
):
    """Download one or multiple audio tracks (via --file)."""

    settings = Settings.load()

    final_ext = ext or settings.get("ext_audio")
    final_bitrate = bitrate or settings.get("bitrate")
    final_threads = threads or settings.get("threads")
    final_path = output_path or settings.get("output_path")
    final_proxy = proxy or settings.get("proxy")
    final_cookie = cookie or settings.get("cookie")
    final_archive = archive or settings.get("archive")
    final_rate_limit = limit or settings.get("limit")

    urls = [url] if url else []
    if input_file:
        urls.extend(Path(input_file).read_text(encoding="utf-8").splitlines())

    if not urls:
        typer.secho("Error: Provide a URL or a --file containing URLs.", fg="red")
        raise typer.Exit(1)

    default_tmpl = str(BASE_DIR / "VEXT" / "Audios" / "%(title)s.%(ext)s")
    tmpl = str(Path(final_path) / "%(title)s.%(ext)s") if final_path else default_tmpl

    config = AudioConfig(
        audio_format=final_ext,
        audio_quality=final_bitrate,
        outtmpl=tmpl,
        concurrent_fragment_downloads=final_threads,
        writethumbnail=write_thumb,
        writedescription=write_desc,
        writeinfojson=write_json,
        embedthumbnail=thumb,
        embedmetadata=meta,
        proxy=final_proxy,
        cookiefile=final_cookie,
        ratelimit=final_rate_limit,
        download_archive=final_archive,
        verbose=verbose,
    )

    with Engine(config=config) as engine:
        for target_url in urls:
            if not target_url.strip():
                continue

            if engine.download(target_url.strip()):
                typer.secho("Download Complete!", fg=typer.colors.GREEN, bold=True)
            else:
                raise typer.Exit(code=1)


@audio_app.command("info")
def audio_info(
    url: Annotated[str, typer.Argument(help="The URL of the audio track.")],
    check_thumb: Annotated[
        bool,
        typer.Option("--fetch-thumb", help="Show thumbnail URL if available."),
    ] = False,
    check_meta: Annotated[
        bool,
        typer.Option(
            "--fetch-meta", help="Show extended metadata (artist, album, genre)."
        ),
    ] = False,
    proxy: Annotated[str | None, typer.Option("--proxy", help="Proxy URL.")] = None,
    cookie: Annotated[
        str | None, typer.Option("--cookie", help="Path to cookies file.")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show raw technical extractor data.")
    ] = False,
):
    """Fetch and display rich audio metadata without writing any files."""

    config = AudioConfig(proxy=proxy, cookiefile=cookie, verbose=verbose)

    with Engine(config=config) as engine:
        info = engine.get_info(url)

    if not info:
        typer.secho("Could not fetch audio info.", fg=typer.colors.RED)
        raise typer.Exit(1)

    # --- Core identity ---
    title = info.get("title", "Unknown")
    video_id = info.get("id", "N/A")
    uploader = info.get("uploader") or info.get("channel", "Unknown")
    channel_url = info.get("channel_url") or info.get("uploader_url", "")
    upload_date_raw = info.get("upload_date", "")
    upload_date = (
        f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:]}"
        if len(upload_date_raw) == 8
        else "N/A"
    )

    # --- Stats ---
    duration_str = info.get("duration_string") or _fmt_seconds(info.get("duration"))
    view_count = info.get("view_count")
    like_count = info.get("like_count")

    # --- Description snippet ---
    description = (info.get("description") or "").strip()
    desc_snippet = (description[:200] + "…") if len(description) > 200 else description

    # --- Thumbnail ---
    thumbnail = info.get("thumbnail", "N/A")

    # --- Extended meta ---
    artist = info.get("artist") or info.get("creator") or uploader
    album = info.get("album", "N/A")
    genre = info.get("genre", "N/A")
    track = info.get("track", "N/A")

    # --- Chapters ---
    chapters: list[dict] = info.get("chapters") or []

    # --- Best audio format info ---
    formats: list[dict] = info.get("formats") or []
    audio_formats = [
        f
        for f in formats
        if f.get("acodec")
        and f.get("acodec") != "none"
        and not f.get("vcodec")
        or f.get("vcodec") == "none"
    ]
    best_abr = max((f.get("abr") or 0 for f in audio_formats), default=None)

    # --- Header panel ---
    header = Text()
    header.append(f"{title}\n", style="bold cyan")
    header.append(f"ID: ", style="dim")
    header.append(f"{video_id}\n", style="white")
    header.append(f"Uploader: ", style="dim")
    header.append(f"{uploader}", style="yellow")
    if channel_url:
        header.append(f"  ({channel_url})", style="dim")
    rprint(Panel(header, title="[bold blue]Audio Info[/bold blue]", expand=False))

    # --- Stats table ---
    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column("Key", style="dim", no_wrap=True)
    stats.add_column("Value", style="white")

    stats.add_row("Duration", duration_str)
    stats.add_row("Uploaded", upload_date)
    stats.add_row("Views", f"{view_count:,}" if view_count is not None else "N/A")
    stats.add_row("Likes", f"{like_count:,}" if like_count is not None else "N/A")
    if best_abr:
        stats.add_row("Best Audio Bitrate", f"{int(best_abr)} kbps")
    if desc_snippet:
        stats.add_row("Description", desc_snippet)

    rprint(stats)

    # --- Extended metadata ---
    if check_meta:
        rprint("\n[bold]Extended Metadata[/bold]")
        meta_table = Table(show_header=False, box=None, padding=(0, 2))
        meta_table.add_column("Key", style="dim", no_wrap=True)
        meta_table.add_column("Value", style="white")
        meta_table.add_row("Artist", artist)
        meta_table.add_row("Album", album)
        meta_table.add_row("Track", track)
        meta_table.add_row("Genre", genre)
        rprint(meta_table)

    # --- Thumbnail ---
    if check_thumb:
        rprint(f"\n[bold]Thumbnail URL:[/bold] [link={thumbnail}]{thumbnail}[/link]")

    # --- Chapters ---
    if chapters:
        rprint(f"\n[bold]Chapters[/bold] ({len(chapters)} total)")
        ch_table = Table(show_header=True, header_style="bold magenta", box=None)
        ch_table.add_column("#", style="dim", width=4)
        ch_table.add_column("Start", style="cyan", width=10)
        ch_table.add_column("Title")
        for i, ch in enumerate(chapters, 1):
            ch_table.add_row(
                str(i),
                _fmt_seconds(ch.get("start_time")),
                ch.get("title", ""),
            )
        rprint(ch_table)

    # --- Available audio formats ---
    if audio_formats:
        rprint(f"\n[bold]Available Audio Streams[/bold] ({len(audio_formats)} found)")
        af_table = Table(
            show_header=True, header_style="bold magenta", box=None, padding=(0, 1)
        )
        af_table.add_column("ID", style="cyan", no_wrap=True)
        af_table.add_column("Ext", style="yellow", width=6)
        af_table.add_column("Bitrate", width=10)
        af_table.add_column("Codec", width=10)
        af_table.add_column("Sample Rate", width=12)
        af_table.add_column("Size")

        for f in sorted(audio_formats, key=lambda x: x.get("abr") or 0, reverse=True):
            abr = f.get("abr")
            size_bytes = f.get("filesize") or f.get("filesize_approx")
            af_table.add_row(
                f.get("format_id", "?"),
                f.get("ext", "?"),
                f"{int(abr)} kbps" if abr else "?",
                (f.get("acodec") or "?")[:10],
                f"{f.get('asr', '?')} Hz" if f.get("asr") else "?",
                _fmt_bytes(size_bytes) if size_bytes else "?",
            )
        rprint(af_table)


# --- Helpers ---


def _fmt_seconds(seconds: int | float | None) -> str:
    if seconds is None:
        return "N/A"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _fmt_bytes(num: int | float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"
