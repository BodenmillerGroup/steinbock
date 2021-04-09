import click

from steinbock.measurement.cells._cli import cells
from steinbock.measurement.dists._cli import dists
from steinbock.measurement.graphs._cli import graphs
from steinbock.utils import cli


@click.group(
    cls=cli.OrderedClickGroup,
    help="Extract single-cell data from cell masks",
)
def measure():
    pass


measure.add_command(cells)
measure.add_command(dists)
measure.add_command(graphs)
