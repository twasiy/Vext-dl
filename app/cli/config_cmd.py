from typing import Annotated

import typer
from core import Settings
from rich import print as rprint
from rich.table import Table

config_app = typer.Typer(help="Manage global defaults and environment settings.")


@config_app.command("set")
def set_config(
    key: Annotated[str, typer.Argument(help="The key to modify.")],
    value: Annotated[str, typer.Argument(help="The new value.")],
):
    """Update a setting. Use 'config show' to see available keys."""

    allowed_keys = Settings.get_allowed_keys()

    if key not in allowed_keys:
        typer.secho(f"Invalid key: '{key}'", fg="red", bold=True)
        typer.echo(f"Allowed keys are: {', '.join(allowed_keys)}")
        raise typer.Exit(1)

    # Convert to int if it looks like a number (e.g. bitrate, threads, limit)
    parsed_value: str | int | None = value
    if value.lower() == "none":
        parsed_value = None
    elif value.isdigit():
        parsed_value = int(value)

    Settings.save(key, parsed_value)
    typer.secho(f"Setting '{key}' is now saved as: {parsed_value}", fg="green")


@config_app.command("show")
def show_config():
    """List all adjustable settings and their current values."""

    settings = Settings.load()
    descriptions = Settings.DESCRIPTIONS

    table = Table(title="Vext Settings Manager", show_lines=True)
    table.add_column("Key (Use in 'set')", style="yellow", no_wrap=True)
    table.add_column("Current Value", style="green")
    table.add_column("Description", style="white")

    for key in Settings.get_allowed_keys():
        val = str(settings.get(key, "Not Set"))
        desc = descriptions.get(key, "No description available.")
        table.add_row(key, val, desc)

    rprint(table)
    rprint("\n[dim]Usage: Vext config set <key> <value>[/dim]")
