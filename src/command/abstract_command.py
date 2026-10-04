import copy
import functools
from abc import ABC, abstractmethod

import click


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

    各 command 自己宣告並接收所需的 pipeline（由 CommandContainer 注入），彼此不共用實作。
    註冊時用 main.add_command(SomeCommand(...).handle)
    """

    @abstractmethod
    def handle(self, *args, **kwargs) -> None:
        """command 的進入點，參數由子類別的 click.option 決定"""
