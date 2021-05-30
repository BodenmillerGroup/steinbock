import click
import networkx as nx

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.export.graphs import graphs


@click.group(
    name="graphs",
    cls=cli.OrderedClickGroup,
    help="Spatial object graph export",
)
def graphs_cmd_group():
    pass


@graphs_cmd_group.command(
    name="networkx",
    help="Export spatial object graphs using networkx",
)
@click.option(
    "--graph",
    "graph_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to graph directory",
)
@click.option(
    "--data",
    "data_dirs",
    multiple=True,
    type=click.STRING,
    help="Object data (e.g., intensities, regionprops) to use as attributes",
)
@click.option(
    "--format",
    "networkx_format",
    type=click.Choice(["graphml", "gexf", "gml"], case_sensitive=False),
    default="graphml",
    show_default=True,
    help="AnnData file format to use",
)
@click.option(
    "--dest",
    "networkx_dir",
    type=click.Path(file_okay=False),
    default=cli.default_networkx_dir,
    show_default=True,
    help="Path to the networkx output directory",
)
@check_version
def networkx_cmd(graph_dir, data_dirs, networkx_format, networkx_dir):
    networkx_dir = Path(networkx_dir)
    networkx_dir.mkdir(exist_ok=True)
    for graph_file, g in graphs.to_networkx_from_disk(
        io.list_graph_files(graph_dir),
        *[io.list_data_files(data_dir) for data_dir in data_dirs],
    ):
        networkx_file = networkx_dir / graph_file.name
        if networkx_format == "graphml":
            networkx_file = networkx_file.with_suffix(".graphml")
            nx.write_graphml(g, str(networkx_file))
        elif networkx_format == "gexf":
            networkx_file = networkx_file.with_suffix(".gexf")
            nx.write_gexf(g, str(networkx_file))
        elif networkx_format == 'gml':
            networkx_file = networkx_file.with_suffix(".gml")
            nx.write_gml(g, str(networkx_file))
        click.echo(networkx_file)
