import click

from pathlib import Path

from steinbock import io
from steinbock._env import check_steinbock_version
from steinbock.measurement import graphs


@click.command(name="graphs", help="Construct spatial object graphs")
@click.option(
    "--masks",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask directory",
)
@click.option(
    "--type",
    "graph_type",
    type=click.Choice(choices=["centroid", "border", "expand"]),
    required=True,
    help="Graph construction method",
)
@click.option(
    "--metric",
    "metric",
    type=click.STRING,
    default="euclidean",
    help="Spatial distance metric (see scipy's pdist)",
)
@click.option(
    "--dmax",
    "dmax",
    type=click.FLOAT,
    help="Maximum spatial distance between objects",
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
def graphs_cmd(mask_dir, graph_type, metric, dmax, kmax, graph_dir):
    mask_files = io.list_mask_files(mask_dir)
    Path(graph_dir).mkdir(exist_ok=True)
    for mask_file, graph in graphs.construct_graphs_from_disk(
        mask_files, graph_type, metric=metric, dmax=dmax, kmax=kmax
    ):
        graph_stem = Path(graph_dir) / Path(mask_file).stem
        graph_file = io.write_graph(graph, graph_stem)
        click.echo(graph_file)
        del graph
