import click
import networkx as nx

from fcswrite import write_fcs
from pathlib import Path
from xtiff import to_tiff

from steinbock import io
from steinbock._cli.utils import OrderedClickGroup
from steinbock._env import check_steinbock_version
from steinbock.export import data, graphs


@click.group(
    name="export",
    cls=OrderedClickGroup,
    help="Export data to third-party formats",
)
def export_cmd_group():
    pass


@export_cmd_group.command(name="ome", help="Export images as OME-TIFF")
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel file",
)
@click.option(
    "-o",
    "ome_dir",
    type=click.Path(file_okay=False),
    default="ome",
    show_default=True,
    help="Path to the OME-TIFF export directory",
)
@check_steinbock_version
def ome_cmd(img_dir, panel_file, ome_dir):
    panel = io.read_panel(panel_file)
    channel_names = panel["name"].tolist()
    Path(ome_dir).mkdir(exist_ok=True)
    for img_file in io.list_image_files(img_dir):
        img = io.read_image(img_file)
        ome_file = io.as_path_with_suffix(
            Path(ome_dir) / img_file.name, ".ome.tiff"
        )
        to_tiff(img, ome_file, channel_names=channel_names)
        click.echo(ome_file.name)
        del img


@export_cmd_group.command(
    name="csv", help="Collect object data into a single CSV file"
)
@click.argument(
    "data_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "-o",
    "csv_file",
    type=click.Path(dir_okay=False),
    default="objects.csv",
    show_default=True,
    help="Path to the CSV output file",
)
@check_steinbock_version
def csv_cmd(data_dirs, csv_file):
    if not data_dirs:
        return  # empty variadic argument, gracefully degrade into noop
    first_data_files = io.list_data_files(data_dirs[0])
    data_file_lists = [first_data_files]
    for data_dir in data_dirs[1:]:
        data_files = io.list_data_files(data_dir, base_files=first_data_files)
        data_file_lists.append(data_files)
    df = data.try_convert_to_dataframe_from_disk(*data_file_lists)
    df.reset_index(inplace=True)
    df.to_csv(csv_file, index=False)


@export_cmd_group.command(
    name="fcs",
    help="Collect object data into a single FCS file",
)
@click.argument(
    "data_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "-o",
    "fcs_file",
    type=click.Path(dir_okay=False),
    default="objects.fcs",
    show_default=True,
    help="Path to the FCS output file",
)
@check_steinbock_version
def fcs_cmd(data_dirs, fcs_file):
    if not data_dirs:
        return  # empty variadic argument, gracefully degrade into noop
    first_data_files = io.list_data_files(data_dirs[0])
    data_file_lists = [first_data_files]
    for data_dir in data_dirs[1:]:
        data_files = io.list_data_files(data_dir, base_files=first_data_files)
        data_file_lists.append(data_files)
    df = data.try_convert_to_dataframe_from_disk(*data_file_lists)
    write_fcs(fcs_file, df.columns.values, df.values)


@export_cmd_group.command(
    name="anndata", help="Export object data as AnnData files"
)
@click.option(
    "--x",
    "data_dir",
    type=click.Path(exists=True, file_okay=False),
    default="intensities",
    show_default=True,
    help="Path to the main data directory",
)
@click.option(
    "--obs",
    "obs_data_dirs",
    multiple=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path to the object regionprops directory",
)
@click.option(
    "--format",
    "anndata_format",
    type=click.Choice(["h5ad", "loom", "zarr"], case_sensitive=False),
    default="h5ad",
    show_default=True,
    help="AnnData file format to use",
)
@click.option(
    "-o",
    "anndata_dir",
    type=click.Path(file_okay=False),
    default="anndata",
    show_default=True,
    help="Path to the AnnData output directory",
)
@check_steinbock_version
def anndata_cmd(data_dir, obs_data_dirs, anndata_dir, anndata_format):
    data_files = io.list_data_files(data_dir)
    obs_data_file_lists = [
        io.list_data_files(obs_data_dir, base_files=data_files)
        for obs_data_dir in obs_data_dirs
    ]
    Path(anndata_dir).mkdir(exist_ok=True)
    for data_file, anndata in data.try_convert_to_anndata_from_disk(
        data_files, *obs_data_file_lists
    ):
        anndata_file = Path(anndata_dir) / data_file.name
        if anndata_format.lower() == "h5ad":
            anndata_file = io.as_path_with_suffix(anndata_file, ".h5ad")
            anndata.write_h5ad(anndata_file)
        elif anndata_format.lower() == "loom":
            anndata_file = io.as_path_with_suffix(anndata_file, ".loom")
            anndata.write_loom(anndata_file)
        elif anndata_format.lower() == "zarr":
            anndata_file = io.as_path_with_suffix(anndata_file, ".zarr")
            anndata.write_zarr(anndata_file)
        else:
            raise NotImplementedError()
        click.echo(anndata_file)


@export_cmd_group.command(
    name="graphs", help="Export neighbors as spatial object graphs"
)
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
    for neighbors_file, graph in graphs.try_convert_to_networkx_from_disk(
        neighbors_files, *data_file_lists
    ):
        graph_file = Path(graph_dir) / neighbors_file.name
        if graph_format == "graphml":
            graph_file = io.as_path_with_suffix(graph_file, ".graphml")
            nx.write_graphml(graph, str(graph_file))
        elif graph_format == "gexf":
            graph_file = io.as_path_with_suffix(graph_file, ".gexf")
            nx.write_gexf(graph, str(graph_file))
        elif graph_format == "gml":
            graph_file = io.as_path_with_suffix(graph_file, ".gml")
            nx.write_gml(graph, str(graph_file))
        else:
            raise NotImplementedError()
        click.echo(graph_file)
