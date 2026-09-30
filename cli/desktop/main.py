import click

from container.desktop import DesktopContainer
from src.app import desktop


@click.command(name="desktop")
def main():
    """Run the desktop app."""
    desktop.run(DesktopContainer())


if __name__ == "__main__":
    main()
