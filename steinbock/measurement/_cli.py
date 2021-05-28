import click

from steinbock import cli
from steinbock.measurement.cellprofiler._cli import cellprofiler_cmd_group
from steinbock.measurement.dists._cli import distances_cmd_group
from steinbock.measurement.graphs._cli import graphs_cmd
from steinbock.measurement.intensities._cli import intensities_cmd
from steinbock.measurement.regionprops._cli import regionprops_cmd


@click.group(
    name="measure",
    cls=cli.OrderedClickGroup,
    help="Extract object data from segmented images",
)
def measure_cmd_group():
    pass


measure_cmd_group.add_command(intensities_cmd)
measure_cmd_group.add_command(regionprops_cmd)
measure_cmd_group.add_command(distances_cmd_group)
measure_cmd_group.add_command(graphs_cmd)
measure_cmd_group.add_command(cellprofiler_cmd_group)
