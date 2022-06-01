from collections import OrderedDict
from typing import Dict

import click
from click.core import Command


class OrderedClickGroup(click.Group):
    def __init__(self, *args, commands=None, **kwargs) -> None:
        super(OrderedClickGroup, self).__init__(*args, **kwargs)
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx) -> Dict[str, Command]:
        return self.commands
