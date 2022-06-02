import logging
from collections import OrderedDict
from functools import partial, wraps
from typing import Dict

import click
from click.core import Command

from .._steinbock import SteinbockException


logger = logging.getLogger(__name__.rpartition(".")[0].rpartition(".")[0])


class SteinbockCLIException(SteinbockException):
    pass


class OrderedClickGroup(click.Group):
    def __init__(self, *args, commands=None, **kwargs) -> None:
        super(OrderedClickGroup, self).__init__(*args, **kwargs)
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx) -> Dict[str, Command]:
        return self.commands


def catch_exception(func=None, *, handle=SteinbockException):
    if not func:
        return partial(catch_exception, handle=handle)

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except handle as e:
            raise click.ClickException(e)

    return wrapper
