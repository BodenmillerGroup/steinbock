import click

from steinbock._cli.utils import OrderedClickGroup
from steinbock.measurement._cli.cellprofiler import cellprofiler_cmd_group
from steinbock.measurement._cli.intensities import intensities_cmd
from steinbock.measurement._cli.neighbors import neighbors_cmd
from steinbock.measurement._cli.regionprops import regionprops_cmd


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
