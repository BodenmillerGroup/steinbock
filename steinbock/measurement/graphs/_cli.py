import click

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.measurement.graphs import graphs


@click.command(
    name="graphs",
    help="Construct spatial object neighborhood graphs",
)
@click.option(
    "--dists",
    "dists_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_dists_dir,
    show_default=True,
    help="Path to the object distances directory",
)
@click.option(
    "--dmax",
    "dmax",
    type=click.FLOAT,
    help="Maximum distance between objects",
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
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to the object graph output directory",
)
@check_version
def graphs_cmd(dists_dir, dmax, kmax, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    for dists_file, df in graphs.construct_graphs_from_disk(
        io.list_dists_files(dists_dir),
        dmax=dmax,
        kmax=kmax,
    ):
        graph_file = io.write_graph(df, graph_dir / Path(dists_file).stem)
        click.echo(graph_file)
        del df
