import click

from cli import desktop


@click.group()
def cli():
    """Landan Desktop command line."""


cli.add_command(desktop.main, name="desktop")


if __name__ == "__main__":
    cli()
