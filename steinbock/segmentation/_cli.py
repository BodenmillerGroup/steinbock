import click

from steinbock import cli
from steinbock.segmentation.cellprofiler._cli import cellprofiler_cmd_group
from steinbock.segmentation.deepcell._cli import deepcell_cmd


@click.group(
    name="segment",
    cls=cli.OrderedClickGroup,
    help="Perform image segmentation to create object masks",
)
def segment_cmd_group():
    pass


segment_cmd_group.add_command(cellprofiler_cmd_group)
segment_cmd_group.add_command(deepcell_cmd)
