import click

from steinbock.measurement.cells._cli import cells_cmd
from steinbock.measurement.dists._cli import dists_cmd
from steinbock.measurement.graphs._cli import graphs_cmd
from steinbock.measurement.cellprofiler._cli import cellprofiler_cmd
from steinbock.utils import cli


@click.group(
    cls=cli.OrderedClickGroup,
    help="Extract single-cell data from segmented cells",
)
def measure():
    pass


measure.add_command(cells_cmd)
measure.add_command(dists_cmd)
measure.add_command(graphs_cmd)
measure.add_command(cellprofiler_cmd)
