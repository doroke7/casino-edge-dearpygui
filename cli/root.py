import click

from cli import desktop, recognition


@click.group()
def root():
    """Commands collected for main."""


root.add_command(desktop.main, name="desktop")
root.add_command(recognition.main)
