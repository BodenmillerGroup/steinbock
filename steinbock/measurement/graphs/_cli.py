import click

from pathlib import Path

from steinbock.measurement.graphs import graphs
from steinbock.utils import cli, io


@click.group(
    name="graphs",
    cls=cli.OrderedClickGroup,
    help="Construct spatial cell neighborhood graphs",
)
def graphs_cmd():
    pass


@graphs_cmd.command(
    help="Construct directed spatial k-nearest neighbor graphs",
)
@click.option(
    "--dists",
    "cell_dists_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_cell_dists_dir,
    show_default=True,
    help="Path to the cell distances directory",
)
@click.option(
    "--k",
    "k",
    type=click.INT,
    required=True,
    help="Number of neighbors per cell",
)
@click.option(
    "--dest",
    "cell_graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_cell_graph_dir,
    show_default=True,
    help="Path to the cell graph output directory",
)
def knn(cell_dists_dir, k, cell_graph_dir):
    cell_graph_dir = Path(cell_graph_dir)
    cell_graph_dir.mkdir(exist_ok=True)
    cell_dists_files = io.list_cell_dists(cell_dists_dir)
    for cell_dists_file, cell_graph in graphs.construct_knn_graphs(
        cell_dists_files,
        k,
    ):
        cell_graph_file = cell_graph_dir / Path(cell_dists_file).stem
        cell_graph_file = io.write_cell_graph(cell_graph, cell_graph_file)
        click.echo(cell_graph_file)
        del cell_graph


@graphs_cmd.command(
    help="Construct undirected graphs by thresholding cell border distances",
)
@click.option(
    "--dists",
    "cell_dists_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_cell_dists_dir,
    show_default=True,
    help="Path to the cell distances directory",
)
@click.option(
    "--thres",
    "cell_dist_thres",
    type=click.FLOAT,
    required=True,
    help="Cell border distance threshold",
)
@click.option(
    "--dest",
    "cell_graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_cell_graph_dir,
    show_default=True,
    help="Path to the cell graph output directory",
)
def dist(cell_dists_dir, cell_dist_thres, cell_graph_dir):
    cell_graph_dir = Path(cell_graph_dir)
    cell_graph_dir.mkdir(exist_ok=True)
    cell_dists_files = io.list_cell_dists(cell_dists_dir)
    for cell_dists_file, cell_graph in graphs.construct_dist_graphs(
        cell_dists_files,
        cell_dist_thres,
    ):
        cell_graph_file = cell_graph_dir / Path(cell_dists_file).stem
        cell_graph_file = io.write_cell_graph(cell_graph, cell_graph_file)
        click.echo(cell_graph_file)
        del cell_graph
