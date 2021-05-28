import click

from steinbock import cli
from steinbock.tools.masks._cli import masks_cmd_group
from steinbock.tools.mosaics._cli import mosaics_cmd_group


@click.group(
    name="tools",
    cls=cli.OrderedClickGroup,
    help="Various utilities and tools"
)
def tools_cmd_group():
    pass


tools_cmd_group.add_command(masks_cmd_group)
tools_cmd_group.add_command(mosaics_cmd_group)
