import click

from cli import desktop, recognition


@click.group()
def cli():
    """Landan Desktop command line."""


cli.add_command(desktop.main, name="desktop")
cli.add_command(recognition.main)


if __name__ == "__main__":
    cli()
