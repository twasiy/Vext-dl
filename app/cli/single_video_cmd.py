from pathlib import Path
from typing import Annotated

import typer
from core import BASE_DIR, Engine, Settings, VideoConfig, VideoContainer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

video_app = typer.Typer(help="Download high-quality video files.")
console = Console()


@video_app.command("get")
def download_video(
    url: Annotated[
        str | None,
        typer.Argument(help="The URL to download. Optional if --file is used."),
    ] = None,
    input_file: Annotated[
        str | None, typer.Option("--file", "-f", help="Text file with URLs.")
    ] = None,
    res: Annotated[
        str | None,
        typer.Option(
            "--res", help="Preferred maximum resolution (e.g., 1080p, 2160p, best)."
        ),
    ] = None,
    ext: Annotated[
        VideoContainer | None,
        typer.Option("--ext", help="Preferred video container format."),
    ] = None,
    threads: Annotated[
        int | None,
        typer.Option("--threads", "-t", help="Number of concurrent download threads."),
    ] = None,
    output_path: Annotated[
        str | None,
        typer.Option("--path", "-p", help="Directory where the video will be stored."),
    ] = None,
    write_subs: Annotated[
        bool, typer.Option("--write-subs", help="Write subtitle files to disk.")
    ] = False,
    write_auto_subs: Annotated[
        bool,
        typer.Option(
            "--write-auto-subs", help="Write automatically generated captions."
        ),
    ] = False,
    write_thumb: Annotated[
        bool, typer.Option("--write-thumb", help="Write thumbnail image to disk.")
    ] = False,
    write_desc: Annotated[
        bool, typer.Option("--write-desc", help="Write description file.")
    ] = False,
    thumb: Annotated[
        bool, typer.Option("--thumb", help="Download and embed the video thumbnail.")
    ] = False,
    meta: Annotated[
        bool,
        typer.Option("--meta", "-m", help="Embed technical and descriptive metadata."),
    ] = False,
    subs: Annotated[
        bool, typer.Option("--subs", help="Fetch and embed available subtitle tracks.")
    ] = False,
    proxy: Annotated[
        str | None, typer.Option("--proxy", help="Network proxy URL.")
    ] = None,
    cookie: Annotated[
        str | None, typer.Option("--cookie", help="Path to session cookies file.")
    ] = None,
    limit: Annotated[
        int | None, typer.Option("--limit", help="Restrict download speed (bytes/sec).")
    ] = None,
    archive: Annotated[
        str | None,
        typer.Option(
            "--archive",
            "-a",
            help="File to log downloaded IDs and prevent re-downloads.",
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show full technical logs.")
    ] = False,
):
    """Download one or multiple videos (via --file)."""

    settings = Settings.load()

    final_res = res or settings.get("res")
    final_ext = ext or settings.get("ext_video")
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
        typer.secho("Error: Provide a URL or a --file.", fg="red")
        raise typer.Exit(1)

    default_tmpl = str(BASE_DIR / "VEXT" / "Videos" / "%(title)s.%(ext)s")
    tmpl = str(Path(final_path) / "%(title)s.%(ext)s") if final_path else default_tmpl

    config = VideoConfig(
        resolution=final_res,
        container=final_ext,
        outtmpl=tmpl,
        concurrent_fragment_downloads=final_threads,
        writesubtitles=write_subs,
        writeautomaticsub=write_auto_subs,
        writethumbnail=write_thumb,
        writedescription=write_desc,
        embedthumbnail=thumb,
        embedmetadata=meta,
        embedsubs=subs,
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


@video_app.command("info")
def video_info(
    url: Annotated[str, typer.Argument(help="The URL of the video.")],
    fetch_subs: Annotated[
        bool,
        typer.Option("--fetch-subs", help="List all available subtitle languages."),
    ] = False,
    fetch_formats: Annotated[
        bool,
        typer.Option(
            "--fetch-formats", help="List all available resolutions and format IDs."
        ),
    ] = False,
    proxy: Annotated[str | None, typer.Option("--proxy", help="Proxy URL.")] = None,
    cookie: Annotated[
        str | None, typer.Option("--cookie", help="Path to cookies file.")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show full technical data.")
    ] = False,
):
    """Display rich video details and available formats without downloading."""

    config = VideoConfig(proxy=proxy, cookiefile=cookie, verbose=verbose)

    with Engine(config=config) as engine:
        info = engine.get_info(url)

    if not info:
        typer.secho("Could not fetch video info.", fg=typer.colors.RED)
        raise typer.Exit(1)

    # --- Core identity ---
    title = info.get("title", "Unknown")
    video_id = info.get("id", "N/A")
    uploader = info.get("uploader") or info.get("channel", "Unknown")
    channel_url = info.get("channel_url") or info.get("uploader_url", "")
    upload_date_raw = info.get("upload_date", "")  # "YYYYMMDD"
    upload_date = (
        f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:]}"
        if len(upload_date_raw) == 8
        else "N/A"
    )

    # --- Stats ---
    duration_str = info.get("duration_string") or _fmt_seconds(info.get("duration"))
    view_count = info.get("view_count")
    like_count = info.get("like_count")
    age_limit = info.get("age_limit", 0)

    # --- Description (first 200 chars) ---
    description = (info.get("description") or "").strip()
    desc_snippet = (description[:200] + "…") if len(description) > 200 else description

    # --- Thumbnail ---
    thumbnail = info.get("thumbnail", "N/A")

    # --- Chapters ---
    chapters: list[dict] = info.get("chapters") or []

    # --- Header panel ---
    header = Text()
    header.append(f"{title}\n", style="bold cyan")
    header.append(f"ID: ", style="dim")
    header.append(f"{video_id}\n", style="white")
    header.append(f"Channel: ", style="dim")
    header.append(f"{uploader}", style="yellow")
    if channel_url:
        header.append(f"  ({channel_url})", style="dim")
    rprint(Panel(header, title="[bold blue]Video Info[/bold blue]", expand=False))

    # --- Stats table ---
    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column("Key", style="dim", no_wrap=True)
    stats.add_column("Value", style="white")

    stats.add_row("Duration", duration_str)
    stats.add_row("Uploaded", upload_date)
    stats.add_row("Views", f"{view_count:,}" if view_count is not None else "N/A")
    stats.add_row("Likes", f"{like_count:,}" if like_count is not None else "N/A")
    stats.add_row(
        "Age Limit",
        f"[red]{age_limit}+[/red]" if age_limit else "[green]None[/green]",
    )
    stats.add_row("Thumbnail", thumbnail)

    if desc_snippet:
        stats.add_row("Description", desc_snippet)

    rprint(stats)

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

    # --- Subtitles ---
    if fetch_subs:
        subtitles: dict = info.get("subtitles", {})
        auto_subs: dict = info.get("automatic_captions", {})
        all_langs = sorted(set(list(subtitles.keys()) + list(auto_subs.keys())))
        if all_langs:
            manual = [lang for lang in all_langs if lang in subtitles]
            auto = [lang for lang in all_langs if lang not in subtitles]
            rprint(f"\n[bold]Subtitles[/bold]")
            if manual:
                rprint(f"  [green]Manual:[/green] {', '.join(manual)}")
            if auto:
                rprint(f"  [dim]Auto-generated:[/dim] {', '.join(auto)}")
        else:
            rprint("\n[dim]No subtitles available.[/dim]")

    # --- Formats ---
    if fetch_formats:
        formats: list[dict] = info.get("formats") or []
        if formats:
            rprint(f"\n[bold]Available Formats[/bold] ({len(formats)} total)")
            fmt_table = Table(
                show_header=True, header_style="bold magenta", box=None, padding=(0, 1)
            )
            fmt_table.add_column("ID", style="cyan", no_wrap=True)
            fmt_table.add_column("Ext", style="yellow", width=6)
            fmt_table.add_column("Resolution", width=12)
            fmt_table.add_column("FPS", width=5)
            fmt_table.add_column("VCodec", width=10)
            fmt_table.add_column("ACodec", width=10)
            fmt_table.add_column("Size", width=10)
            fmt_table.add_column("Note")

            for f in sorted(
                formats,
                key=lambda x: (x.get("height") or 0, x.get("abr") or 0),
                reverse=True,
            ):
                height = f.get("height")
                width = f.get("width")
                res = (
                    f"{width}x{height}"
                    if width and height
                    else (f"{height}p" if height else "audio only")
                )
                size_bytes = f.get("filesize") or f.get("filesize_approx")
                size_str = _fmt_bytes(size_bytes) if size_bytes else "?"

                fmt_table.add_row(
                    f.get("format_id", "?"),
                    f.get("ext", "?"),
                    res,
                    str(int(f.get("fps") or 0)) or "—",
                    (f.get("vcodec") or "none")[:10],
                    (f.get("acodec") or "none")[:10],
                    size_str,
                    f.get("format_note", ""),
                )
            rprint(fmt_table)


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
