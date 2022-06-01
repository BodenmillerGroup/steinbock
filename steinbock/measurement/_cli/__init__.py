import click

from ..._cli.utils import OrderedClickGroup
from .cellprofiler import cellprofiler_cmd_group
from .intensities import intensities_cmd
from .neighbors import neighbors_cmd
from .regionprops import regionprops_cmd


@click.group(
    name="measure",
    cls=OrderedClickGroup,
    help="Extract object data from segmented images",
)
def measure_cmd_group():
    pass


measure_cmd_group.add_command(intensities_cmd)
measure_cmd_group.add_command(regionprops_cmd)
measure_cmd_group.add_command(neighbors_cmd)
measure_cmd_group.add_command(cellprofiler_cmd_group)
