import click

from steinbock.measurement.objects._cli import objects_cmd
from steinbock.measurement.distances._cli import distances_cmd
from steinbock.measurement.graphs._cli import graphs_cmd
from steinbock.measurement.cellprofiler._cli import cellprofiler_cmd
from steinbock.utils import cli


@click.group(
    cls=cli.OrderedClickGroup,
    help="Extract data from segmented objects",
)
def measure():
    pass


measure.add_command(objects_cmd)
measure.add_command(distances_cmd)
measure.add_command(graphs_cmd)
measure.add_command(cellprofiler_cmd)
