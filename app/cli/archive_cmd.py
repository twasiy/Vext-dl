from pathlib import Path
from typing import Annotated

import typer

archive_app = typer.Typer(
    help="Manage the download history (archive) to skip duplicates."
)


@archive_app.command("show")
def show_archive(
    archive_path: Annotated[
        Path, typer.Argument(help="Path to your archive.txt file.")
    ],
):
    """List all video IDs currently stored in the archive."""

    if not archive_path.exists():
        typer.secho("Archive file not found.", fg="red")
        return

    ids = archive_path.read_text().splitlines()
    typer.echo(f"Found {len(ids)} entries in archive:")
    for vid_id in ids[-10:]:  # Show last 10
        typer.echo(f"  - {vid_id}")


@archive_app.command("clear")
def clear_archive(
    archive_path: Annotated[
        Path, typer.Argument(help="Path to the archive file to wipe.")
    ],
):
    """Wipe the archive file to allow re-downloading everything."""

    if typer.confirm("Are you sure you want to clear the download history?"):
        archive_path.write_text("")
        typer.secho("Archive cleared.", fg="green")


@archive_app.command("add")
def add_to_archive(
    path: Annotated[Path, typer.Argument(help="Path to the archive.txt file.")],
    video_id: Annotated[
        str, typer.Option("--id", help="The unique ID of the video to skip.")
    ],
    extractor: Annotated[
        str,
        typer.Option(
            "--site",
            "-s",
            help="The source site/extractor (e.g., youtube, facebook, twitch, instagram).",
        ),
    ] = "youtube",
):
    """
    Manually inject a video ID into the archive for a specific site.
    """
    # yt-dlp expects exactly: "{extractor_name} {id}"
    entry = f"{extractor.lower()} {video_id}\n"

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)
        typer.secho(f"Added {extractor} ID '{video_id}' to archive.", fg="green")
    except Exception as e:
        typer.secho(f"Failed to write to archive: {e}", fg="red")
