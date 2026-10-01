import click

from src.command.abstract_command import AbstractCommand, BoundCommand


class PokerCommand(AbstractCommand):

    @click.command("poker", cls=BoundCommand)
    @click.option("--workdir", "workdir", required=True, type=click.Path(exists=True, file_okay=False))
    @click.option("--threads", "threads", type=click.IntRange(min=1), default=1, show_default=True)
    def handle(self, workdir, threads) -> None:
        """對 workdir 底下每張圖片跑撲克牌辨識並印出結果"""
        self.run_workdir(self.poker_pipeline, workdir, threads)
