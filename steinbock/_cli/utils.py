import click

from collections import OrderedDict


class OrderedClickGroup(click.Group):
    def __init__(self, *args, commands=None, **kwargs):
        super(OrderedClickGroup, self).__init__(*args, **kwargs)
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands
