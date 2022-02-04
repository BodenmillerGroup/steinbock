import click

from .cellprofiler import cellprofiler_cmd_group
from .deepcell import deepcell_cli_available, deepcell_cmd
from ..._cli.utils import OrderedClickGroup


@click.group(
    name="segment",
    cls=OrderedClickGroup,
    help="Perform image segmentation to create object masks",
)
def segment_cmd_group():
    pass


segment_cmd_group.add_command(cellprofiler_cmd_group)
if deepcell_cli_available:
    segment_cmd_group.add_command(deepcell_cmd)
