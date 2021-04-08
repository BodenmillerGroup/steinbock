import click

from pathlib import Path

from steinbock.graphs.graphs import construct_knn_graphs, construct_dist_graphs
from steinbock.utils import cli, io


@click.group(
    cls=cli.OrderedClickGroup,
    help="Construct spatial cell graphs",
)
def graphs():
    pass


@graphs.command(
    help="Construct directed spatial k-nearest neighbor graphs",
)
@click.option(
    "--data",
    "cell_data_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_cell_intensities_dir,
    show_default=True,
    help="Path to the cell data .csv directory",
)
@click.option(
    "--dist",
    "cell_dist_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_cell_dist_dir,
    show_default=True,
    help="Path to the cell distances .nc directory",
)
@click.option(
    "--k",
    "num_cell_neighbors",
    type=click.INT,
    required=True,
    help="Number of neighbors per cell",
)
@click.option(
    "--dest",
    "graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to the graph output directory",
)
def knn(cell_data_dir, cell_dist_dir, num_cell_neighbors, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    cell_data_files = sorted(Path(cell_data_dir).glob("*.csv"))
    cell_dist_files = sorted(Path(cell_dist_dir).glob("*.csv"))
    it = construct_knn_graphs(
        cell_data_files,
        cell_dist_files,
        num_cell_neighbors,
    )
    with click.progressbar(it, length=len(cell_data_files)) as pbar:
        for cell_data_file, cell_dist_file, graph in pbar:
            graph_file_name = Path(cell_data_file).with_suffix(".graphml").name
            io.write_graph(graph, graph_dir / graph_file_name)


@graphs.command(
    help="Construct undirected graphs by thresholding cell border distances",
)
@click.option(
    "--data",
    "cell_data_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_cell_intensities_dir,
    show_default=True,
    help="Path to the cell data .csv directory",
)
@click.option(
    "--dist",
    "cell_dist_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_cell_dist_dir,
    show_default=True,
    help="Path to the cell distances .nc directory",
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
    "graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to the graph output directory",
)
def dist(cell_data_dir, cell_dist_dir, cell_dist_thres, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    cell_data_files = sorted(Path(cell_data_dir).glob("*.csv"))
    cell_dist_files = sorted(Path(cell_dist_dir).glob("*.csv"))
    it = construct_dist_graphs(
        cell_data_files,
        cell_dist_files,
        cell_dist_thres,
    )
    with click.progressbar(it, length=len(cell_data_files)) as pbar:
        for cell_data_file, cell_dist_file, graph in pbar:
            graph_file_name = Path(cell_data_file).with_suffix(".graphml").name
            io.write_graph(graph, graph_dir / graph_file_name)
