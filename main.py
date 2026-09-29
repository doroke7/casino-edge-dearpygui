import click

from cli import root

cli = click.CommandCollection(sources=[root.root], help="Landan Desktop command line.")


if __name__ == "__main__":
    cli()
