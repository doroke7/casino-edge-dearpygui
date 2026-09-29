import click

from cli import root


@click.group()
def cli():
    """Landan Desktop command line."""


for o_command in root.root.commands.values():
    cli.add_command(o_command)


if __name__ == "__main__":
    cli()
