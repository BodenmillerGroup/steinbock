import click

from steinbock._cli.utils import OrderedClickGroup
from steinbock.utils._cli.matching import match_cmd
from steinbock.utils._cli.mosaics import mosaics_cmd_group


@click.group(
    name="utils", cls=OrderedClickGroup, help="Various utilities and tools"
)
def utils_cmd_group():
    pass


utils_cmd_group.add_command(match_cmd)
utils_cmd_group.add_command(mosaics_cmd_group)
