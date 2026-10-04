import click

from container.command import CommandContainer

o_command_container = CommandContainer()


@click.group("command")
def main():
    """Landan Desktop 工具集"""


main.add_command(o_command_container.poker_predictor_command().handle)
main.add_command(o_command_container.die_predictor_command().handle)
