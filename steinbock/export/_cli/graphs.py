import click
import networkx as nx

from pathlib import Path

from steinbock import io
from steinbock._env import check_steinbock_version
from steinbock.export import graphs


@click.command(name="graphs", help="Export neighbors as spatial object graphs")
@click.option(
    "--neighbors",
    "neighbors_dir",
    type=click.Path(exists=True, file_okay=False),
    default="neighbors",
    show_default=True,
    help="Path to the neighbors directory",
)
@click.option(
    "--data",
    "data_dirs",
    multiple=True,
    type=click.STRING,
    help="Object data (e.g. intensities, regionprops) to use as attributes",
)
@click.option(
    "--format",
    "graph_format",
    type=click.Choice(["graphml", "gexf", "gml"], case_sensitive=False),
    default="graphml",
    show_default=True,
    help="AnnData file format to use",
)
@click.option(
    "-o",
    "graph_dir",
    type=click.Path(file_okay=False),
    default="graphs",
    show_default=True,
    help="Path to the networkx output directory",
)
@check_steinbock_version
def graphs_cmd(neighbors_dir, data_dirs, graph_format, graph_dir):
    neighbors_files = io.list_neighbors_files(neighbors_dir)
    data_file_lists = [
        io.list_data_files(data_dir, base_files=neighbors_files)
        for data_dir in data_dirs
    ]
    Path(graph_dir).mkdir(exist_ok=True)
    for (
        neighbors_file,
        data_files,
        graph,
    ) in graphs.try_convert_to_networkx_from_disk(
        neighbors_files, *data_file_lists
    ):
        graph_file = Path(graph_dir) / neighbors_file.name
        if graph_format == "graphml":
            graph_file = io._as_path_with_suffix(graph_file, ".graphml")
            nx.write_graphml(graph, str(graph_file))
        elif graph_format == "gexf":
            graph_file = io._as_path_with_suffix(graph_file, ".gexf")
            nx.write_gexf(graph, str(graph_file))
        elif graph_format == "gml":
            graph_file = io._as_path_with_suffix(graph_file, ".gml")
            nx.write_gml(graph, str(graph_file))
        else:
            raise NotImplementedError()
        click.echo(graph_file)
