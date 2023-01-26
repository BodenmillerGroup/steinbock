import click

from ..._cli.utils import OrderedClickGroup
from .matching import match_cmd
from .mosaics import mosaics_cmd_group


@click.group(name="utils", cls=OrderedClickGroup, help="Various utilities and tools")
def utils_cmd_group():
    pass


utils_cmd_group.add_command(match_cmd)
utils_cmd_group.add_command(mosaics_cmd_group)
