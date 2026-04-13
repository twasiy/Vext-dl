from pathlib import Path
from typing import Annotated, Literal

import typer
from core import BASE_DIR, Engine, PlaylistConfig, PlaylistContainer, Settings
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

playlist_app = typer.Typer(help="Handle entire YouTube playlists.")


@playlist_app.command("get")
def download_playlist(
    url: Annotated[
        str | None, typer.Argument(help="Playlist URL. Optional if --file is used.")
    ] = None,
    input_file: Annotated[
        str | None, typer.Option("--file", "-f", help="Text file with Playlist URLs.")
    ] = None,
    mode: Annotated[
        Literal["video", "audio"],
        typer.Option(
            "--mode",
            help="Download mode: 'video' for full files or 'audio' for extraction.",
        ),
    ] = "video",
    res: Annotated[
        str | None,
        typer.Option(
            "--res",
            help="Preferred maximum resolution for video mode (e.g., 720p, 1080p).",
        ),
    ] = None,
    ext: Annotated[
        PlaylistContainer | None,
        typer.Option("--ext", help="Preferred file extension/container format."),
    ] = None,
    output_path: Annotated[
        str | None,
        typer.Option("--path", "-p", help="Custom base directory for the playlist."),
    ] = None,
    bitrate: Annotated[
        int | None,
        typer.Option(
            "--bitrate", help="Audio bitrate quality (used if mode is 'audio')."
        ),
    ] = None,
    items: Annotated[
        str | None,
        typer.Option(
            "--items",
            "-i",
            help="Specific items to download from the playlist (e.g., '1,2,5-10', 'start:end:step').",
        ),
    ] = None,
    threads: Annotated[
        int | None,
        typer.Option("--threads", "-t", help="Number of concurrent download threads."),
    ] = None,
    write_thumb: Annotated[
        bool, typer.Option("--write-thumb", help="Save thumbnails for every item.")
    ] = False,
    write_desc: Annotated[
        bool,
        typer.Option("--write-desc", help="Save description files for every item."),
    ] = False,
    write_json: Annotated[
        bool, typer.Option("--write-json", help="Save info.json for every item.")
    ] = False,
    thumb: Annotated[
        bool, typer.Option("--thumb", help="Embed video thumbnails as cover art.")
    ] = False,
    meta: Annotated[
        bool,
        typer.Option(
            "--meta", "-m", help="Embed playlist and video metadata into files."
        ),
    ] = False,
    subs: Annotated[
        bool,
        typer.Option(
            "--subs", help="Download and embed available subtitles (video mode only)."
        ),
    ] = False,
    proxy: Annotated[
        str | None,
        typer.Option("--proxy", help="Use a proxy server for the connection."),
    ] = None,
    cookie: Annotated[
        str | None,
        typer.Option(
            "--cookie",
            help="Path to a cookies.txt file for age-restricted or private playlists.",
        ),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option(
            "--limit", help="Global download speed limit in bytes per second."
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show verbose output for debugging.")
    ] = False,
    archive: Annotated[
        str | None,
        typer.Option(
            "--archive",
            "-a",
            help="Path to a tracker file to avoid downloading the same video twice.",
        ),
    ] = None,
):
    """Download one or multiple playlists (via --file)."""

    settings = Settings.load()

    final_res = res or settings.get("res")
    final_ext = ext or settings.get("ext_video")
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
        typer.secho("Error: Provide a URL or a --file.", fg="red")
        raise typer.Exit(1)

    for target_url in urls:
        if not target_url.strip():
            continue

        if final_path:
            save_dir = Path(final_path)
            tmpl = str(save_dir / "%(title)s.%(ext)s")
        else:
            tmpl = str(
                BASE_DIR
                / "VEXT"
                / "Playlists"
                / "%(playlist_title)s"
                / "%(title)s.%(ext)s"
            )

        config = PlaylistConfig(
            mode=mode,
            resolution=final_res,
            container=final_ext,
            outtmpl=tmpl,
            audio_quality=final_bitrate,
            playlist_items=items,
            concurrent_fragment_downloads=final_threads,
            writethumbnail=write_thumb,
            writedescription=write_desc,
            writeinfojson=write_json,
            embedthumbnail=thumb,
            embedmetadata=meta,
            embedsubs=subs,
            proxy=final_proxy,
            cookiefile=final_cookie,
            ratelimit=final_rate_limit,
            download_archive=final_archive,
            verbose=verbose,
            lazy_playlist=True,
        )

        with Engine(config=config) as engine:
            if engine.download(target_url.strip()):
                typer.secho("Playlist download complete!", fg=typer.colors.GREEN)
            else:
                typer.secho("An error occurred while downloading.", fg=typer.colors.RED)


@playlist_app.command("info")
def playlist_info(
    url: Annotated[str, typer.Argument(help="The URL of the playlist.")],
    items: Annotated[
        str | None,
        typer.Option(
            "--items",
            "-i",
            help="Specific range to inspect (e.g. '1-5', 'start:end:step').",
        ),
    ] = None,
    proxy: Annotated[str | None, typer.Option("--proxy", help="Proxy URL.")] = None,
    cookie: Annotated[
        str | None, typer.Option("--cookie", help="Path to cookies file.")
    ] = None,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show full technical data.")
    ] = False,
):
    """View a rich summary of playlist contents."""

    config = PlaylistConfig(
        playlist_items=items,
        proxy=proxy,
        cookiefile=cookie,
        verbose=verbose,
        extract_flat="in_playlist",
    )

    with Engine(config=config) as engine:
        info = engine.get_info(url)

    if not info:
        typer.secho("Could not fetch playlist info.", fg=typer.colors.RED)
        raise typer.Exit(1)

    entries: list[dict] = info.get("entries") or []

    # --- Playlist header ---
    pl_title = info.get("title", "Unknown Playlist")
    pl_uploader = info.get("uploader") or info.get("channel", "Unknown")
    pl_id = info.get("id", "N/A")
    pl_url = info.get("webpage_url", "")
    pl_description = (info.get("description") or "").strip()
    desc_snippet = (
        (pl_description[:200] + "…") if len(pl_description) > 200 else pl_description
    )

    # --- Aggregate stats ---
    total_views = info.get("view_count")
    # Sum entry view counts if playlist-level total isn't available
    if total_views is None:
        entry_views = [e.get("view_count") for e in entries if e.get("view_count")]
        total_views = sum(entry_views) if entry_views else None

    total_duration = sum(
        e.get("duration") or 0 for e in entries if e.get("duration") is not None
    )

    # --- Header panel ---
    header = Text()
    header.append(f"{pl_title}\n", style="bold cyan")
    header.append(f"ID: ", style="dim")
    header.append(f"{pl_id}\n", style="white")
    header.append(f"Uploader: ", style="dim")
    header.append(f"{pl_uploader}", style="yellow")
    if pl_url:
        header.append(f"\n{pl_url}", style="dim")
    rprint(Panel(header, title="[bold blue]Playlist Info[/bold blue]", expand=False))

    # ── Summary stats ---
    stats = Table(show_header=False, box=None, padding=(0, 2))
    stats.add_column("Key", style="dim", no_wrap=True)
    stats.add_column("Value", style="white")

    stats.add_row("Total Items", str(len(entries)))
    if total_duration:
        stats.add_row("Total Duration", _fmt_seconds(total_duration))
    if total_views is not None:
        stats.add_row("Total Views", f"{total_views:,}")
    if desc_snippet:
        stats.add_row("Description", desc_snippet)

    rprint(stats)

    # --- Entry table ---
    if entries:
        rprint(f"\n[bold]Entries[/bold] (showing up to {min(len(entries), 25)})")

        entry_table = Table(
            show_header=True,
            header_style="bold magenta",
            box=None,
            padding=(0, 1),
        )
        entry_table.add_column("#", style="dim", width=4, no_wrap=True)
        entry_table.add_column("Title", style="cyan")
        entry_table.add_column("Uploader", style="yellow", width=20)
        entry_table.add_column("Duration", width=10)
        entry_table.add_column("Views", width=12)
        entry_table.add_column("ID", style="dim", width=14)

        for i, entry in enumerate(entries[:25], 1):
            e_views = entry.get("view_count")
            e_dur = entry.get("duration")
            entry_table.add_row(
                str(i),
                (entry.get("title") or "Unknown")[:60],
                (entry.get("uploader") or entry.get("channel") or "—")[:20],
                _fmt_seconds(e_dur) if e_dur is not None else "?",
                f"{e_views:,}" if e_views is not None else "—",
                entry.get("id", "?"),
            )

        rprint(entry_table)

        if len(entries) > 25:
            rprint(f"\n[dim]… and {len(entries) - 25} more items.[/dim]")


# --- Helpers ---


def _fmt_seconds(seconds: int | float | None) -> str:
    if seconds is None:
        return "N/A"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
