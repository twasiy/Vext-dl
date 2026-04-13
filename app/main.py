import typer
from cli import archive_app, audio_app, config_app, playlist_app, video_app
from rich import print as rprint
from rich.table import Table
from utils import create_initial_dirs

app = typer.Typer(
    rich_markup_mode="rich",
    help="[bold blue]YTFAST[/bold blue]: A high-performance, production-ready media downloader.",
    add_completion=False,
    epilog=(
        "  [bold]Quick Start:[/bold]\n"
        "  [yellow]video get[/yellow] <url> --res 1080p\n"
        "  [yellow]audio get[/yellow] <url> --ext mp3\n\n"
        "Use [bold][command] --help[/bold] for specific subcommand options."
    ),
)


app.add_typer(
    video_app,
    name="video",
    rich_help_panel="Download Engines",
    help="[bold]Video Management[/bold]: Download high-quality videos with customizable resolutions, containers, and subtitle embedding.",
)
app.add_typer(
    audio_app,
    name="audio",
    rich_help_panel="Download Engines",
    help="[bold]Audio Extraction[/bold]: Extract high-fidelity audio tracks from media URLs with support for multiple codecs and metadata tagging.",
)
app.add_typer(
    playlist_app,
    name="playlist",
    rich_help_panel="Download Engines",
    help="[bold]Playlist Operations[/bold]: Batch download entire playlists or albums with smart sub-folder organization and item filtering.",
)
app.add_typer(
    archive_app,
    name="archive",
    rich_help_panel="Maintenance",
    help="[bold]Archive Management[/bold]: Manage the download history to skip duplicates and track local library state.",
)
app.add_typer(
    config_app,
    name="config",
    rich_help_panel="Maintenance",
    help="[bold]Environment Configuration[/bold]: Manage global defaults, persistent settings, and download preferences",
)


@app.command("map", rich_help_panel="Maintenance")
def show_map():
    """Display a full map of every command and subcommand."""
    table = Table(
        title="YTFAST Command Map", show_header=True, header_style="bold magenta"
    )
    table.add_column("Category", style="cyan")
    table.add_column("Subcommand", style="yellow")
    table.add_column("Purpose")

    table.add_row("video", "get | info", "Download video or view meta")
    table.add_row("audio", "get | info", "Extract audio or view meta")
    table.add_row("playlist", "get | info", "Batch process playlists")
    table.add_row("archive", "show | add | clear", "Manage download history")
    table.add_row(
        "config", "show | set", "Manage the tool's behavior and global variable states."
    )

    rprint(table)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-V", help="Show version and exit."
    ),
):
    """
    YTFAST CLI Downloader.
    """
    if version:
        rprint("[bold blue]YTFAST v1.0.0[/bold blue]")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        rprint("[yellow]No command provided. Use --help for usage details.[/yellow]")


if __name__ == "__main__":
    create_initial_dirs()
    app()
