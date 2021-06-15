import click

from pathlib import Path

from steinbock import io
from steinbock._env import check_steinbock_version
from steinbock.measurement import graphs


@click.command(
    name="graphs", help="Construct spatial object neighborhood graphs"
)
@click.option(
    "--dists",
    "dists_dir",
    type=click.Path(exists=True, file_okay=False),
    default="distances",
    show_default=True,
    help="Path to the object distances directory",
)
@click.option(
    "--dmax", "dmax", type=click.FLOAT, help="Maximum distance between objects"
)
@click.option(
    "--kmax",
    "kmax",
    type=click.INT,
    help="Maximum number of neighbors per object",
)
@click.option(
    "--dest",
    "graph_dir",
    type=click.Path(file_okay=False),
    default="graphs",
    show_default=True,
    help="Path to the object graph output directory",
)
@check_steinbock_version
def graphs_cmd(dists_dir, dmax, kmax, graph_dir):
    dists_files = io.list_distances_files(dists_dir)
    Path(graph_dir).mkdir(exist_ok=True)
    for dists_file, graph in graphs.construct_graphs_from_disk(
        dists_files, dmax=dmax, kmax=kmax
    ):
        graph_stem = Path(graph_dir) / Path(dists_file).stem
        graph_file = io.write_graph(graph, graph_stem)
        click.echo(graph_file)
        del graph
