import copy
import functools
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import click
import cv2

from src.pipeline import AbstractPipeline


IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp")


class BoundCommand(click.Command):
    """放在 class body 的 click command：透過實例取用時自動綁定 self

    用法：@click.command("name", cls=BoundCommand)
    """

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        o_bound = copy.copy(self)
        o_bound.callback = functools.partial(self.callback, instance)
        return o_bound


class AbstractCommand(ABC):
    """所有 command 類別的基底：子類別必須實作 handle，並用 @click.command(..., cls=BoundCommand) 裝飾它

    pipeline 由 CommandContainer 建好後注入，command 只管取用。
    註冊時用 main.add_command(SomeCommand(...).handle)
    """

    def __init__(
        self,
        poker_pipeline: AbstractPipeline,
        die_pipeline: AbstractPipeline,
    ) -> None:
        self.poker_pipeline = poker_pipeline
        self.die_pipeline = die_pipeline

    @abstractmethod
    def handle(self, *args, **kwargs) -> None:
        """command 的進入點，參數由子類別的 click.option 決定"""

    def run_workdir(self, pipeline: AbstractPipeline, workdir: str, threads: int) -> None:
        """對 workdir 底下每張圖片跑 pipeline 並依檔名順序印出結果，用 threads 條線程並行推論"""
        paths = sorted(p for p in Path(workdir).iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
        if not paths:
            raise click.ClickException("workdir 底下沒有圖片: " + workdir)

        def infer(path: Path):
            frame_bgr = cv2.imread(str(path))
            if frame_bgr is None:
                return None
            return pipeline.run(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))

        with ThreadPoolExecutor(max_workers=threads) as executor:
            results = executor.map(infer, paths)
            for path, rows in zip(paths, results):
                if rows is None:
                    click.echo("無法讀取圖片: " + str(path))
                    continue

                click.echo(path.name)
                for row in rows:
                    click.echo(row)
