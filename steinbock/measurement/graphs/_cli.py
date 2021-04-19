import click

from pathlib import Path

from steinbock.measurement.graphs import graphs
from steinbock.utils import cli, io


@click.group(
    name="graphs",
    cls=cli.OrderedClickGroup,
    help="Construct spatial object neighborhood graphs",
)
def graphs_cmd():
    pass


@graphs_cmd.command(
    help="Construct directed spatial k-nearest neighbor graphs",
)
@click.option(
    "--dists",
    "distances_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_distances_dir,
    show_default=True,
    help="Path to the object distances directory",
)
@click.option(
    "--k",
    "k",
    type=click.INT,
    required=True,
    help="Number of neighbors per object",
)
@click.option(
    "--dest",
    "graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to the object graph output directory",
)
def knn(distances_dir, k, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    distances_files = io.list_distances(distances_dir)
    it = graphs.construct_knn_graphs(distances_files, k)
    for distances_file, g in it:
        graph_file = io.write_graph(g, graph_dir / Path(distances_file).stem)
        click.echo(graph_file)
        del g


@graphs_cmd.command(
    help="Construct undirected graphs by thresholding on object distances",
)
@click.option(
    "--dists",
    "distances_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_distances_dir,
    show_default=True,
    help="Path to the object distances directory",
)
@click.option(
    "--thres",
    "distance_threshold",
    type=click.FLOAT,
    required=True,
    help="Object distance threshold",
)
@click.option(
    "--dest",
    "graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to the object graph output directory",
)
def dist(distances_dir, distance_threshold, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    distances_files = io.list_distances(distances_dir)
    it = graphs.construct_distance_graphs(distances_files, distance_threshold)
    for distances_file, g in it:
        graph_file = io.write_graph(g, graph_dir / Path(distances_file).stem)
        click.echo(graph_file)
        del g
