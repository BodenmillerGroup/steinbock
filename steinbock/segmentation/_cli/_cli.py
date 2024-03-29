import click

from ..._cli.utils import OrderedClickGroup
from .cellpose import cellpose_cli_available, cellpose_cmd
from .cellprofiler import cellprofiler_cmd_group
from .deepcell import deepcell_cli_available, deepcell_cmd


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
if cellpose_cli_available:
    segment_cmd_group.add_command(cellpose_cmd)
