import click

from cli.desktop import main as desktop
from cli.recognition import main as recognition


@click.group()
def root():
    """Commands collected for main."""


root.add_command(desktop.main, name="desktop")
root.add_command(recognition.main)
