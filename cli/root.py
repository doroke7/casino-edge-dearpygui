import click

from cli.all import main as all_
from cli.desktop import main as desktop
from cli.recognition import main as recognition


@click.group()
def root():
    """Commands collected for main."""


root.add_command(desktop.main, name="desktop")
root.add_command(recognition.main)
root.add_command(all_.main)
