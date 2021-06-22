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
    "--dest",
    "xtiff_dir",
    type=click.Path(file_okay=False),
    default="img_ome",
    show_default=True,
    help="Path to the OME-TIFF export directory",
)
@check_steinbock_version
def ome_cmd(img_dir, panel_file, xtiff_dir):
    panel = io.read_panel(panel_file)
    channel_names = panel["name"].tolist()
    Path(xtiff_dir).mkdir(exist_ok=True)
    for img_file in io.list_image_files(img_dir):
        img = io.read_image(img_file)
        xtiff_file = Path(xtiff_dir) / img_file.with_suffix(".ome.tiff").name
        to_tiff(img, xtiff_file, channel_names=channel_names)
        click.echo(xtiff_file.name)
        del img


@export_cmd_group.command(
    name="csv", help="Collect object data into a single CSV file",
)
@click.argument(
    "data_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "--dest",
    "table_file",
    type=click.Path(dir_okay=False),
    default="objects.csv",
    show_default=True,
    help="Path to the CSV output file",
)
@check_steinbock_version
def csv_cmd(data_dirs, table_file):
    if not data_dirs:
        return  # empty variadic argument, gracefully degrade into noop
    first_data_files = io.list_data_files(data_dirs[0])
    data_file_lists = [first_data_files]
    for data_dir in data_dirs[1:]:
        data_files = io.list_data_files(data_dir, base_files=first_data_files)
        data_file_lists.append(data_files)
    table = data.to_table_from_disk(*data_file_lists)
    table.reset_index(inplace=True)
    table.to_csv(table_file, index=False)


@export_cmd_group.command(
    name="fcs", help="Collect object data into a single FCS file",
)
@click.argument(
    "data_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "--dest",
    "table_file",
    type=click.Path(dir_okay=False),
    default="objects.fcs",
    show_default=True,
    help="Path to the FCS output file",
)
@check_steinbock_version
def fcs_cmd(data_dirs, table_file):
    if not data_dirs:
        return  # empty variadic argument, gracefully degrade into noop
    first_data_files = io.list_data_files(data_dirs[0])
    data_file_lists = [first_data_files]
    for data_dir in data_dirs[1:]:
        data_files = io.list_data_files(data_dir, base_files=first_data_files)
        data_file_lists.append(data_files)
    table = data.to_table_from_disk(*data_file_lists)
    write_fcs(table_file, table.columns.values, table.values)


@export_cmd_group.command(
    name="anndata", help="Export object data as AnnData files"
)
@click.option(
    "--x",
    "x_data_dir",
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
    "--dest",
    "anndata_dir",
    type=click.Path(file_okay=False),
    default="anndata",
    show_default=True,
    help="Path to the AnnData output directory",
)
@check_steinbock_version
def anndata_cmd(x_data_dir, obs_data_dirs, anndata_dir, anndata_format):
    x_data_files = io.list_data_files(x_data_dir)
    obs_data_file_lists = [
        io.list_data_files(obs_data_dir, base_files=x_data_files)
        for obs_data_dir in obs_data_dirs
    ]
    Path(anndata_dir).mkdir(exist_ok=True)
    for x_data_file, ad in data.to_anndata_from_disk(
        x_data_files, *obs_data_file_lists
    ):
        anndata_stem = Path(anndata_dir) / x_data_file.stem
        if anndata_format.lower() == "h5ad":
            anndata_file = anndata_stem.with_suffix(".h5ad")
            ad.write_h5ad(anndata_file)
        elif anndata_format.lower() == "loom":
            anndata_file = anndata_stem.with_suffix(".loom")
            ad.write_loom(anndata_file)
        elif anndata_format.lower() == "zarr":
            anndata_file = anndata_stem.with_suffix(".zarr")
            ad.write_zarr(anndata_file)
        else:
            raise NotImplementedError()
        click.echo(anndata_file)


@export_cmd_group.command(name="graphs", help="Export spatial object graphs")
@click.option(
    "--graph",
    "graph_dir",
    type=click.Path(exists=True, file_okay=False),
    default="graphs",
    show_default=True,
    help="Path to the graph directory",
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
    default="graphs",
    show_default=True,
    help="Path to the networkx output directory",
)
@check_steinbock_version
def graphs_cmd(graph_dir, data_dirs, networkx_format, networkx_dir):
    graph_files = io.list_graph_files(graph_dir)
    data_file_lists = [
        io.list_data_files(data_dir, base_files=graph_files)
        for data_dir in data_dirs
    ]
    Path(networkx_dir).mkdir(exist_ok=True)
    for graph_file, g in graphs.to_networkx_from_disk(
        graph_files, *data_file_lists
    ):
        networkx_stem = Path(networkx_dir) / graph_file.stem
        if networkx_format == "graphml":
            networkx_file = networkx_stem.with_suffix(".graphml")
            nx.write_graphml(g, str(networkx_file))
        elif networkx_format == "gexf":
            networkx_file = networkx_stem.with_suffix(".gexf")
            nx.write_gexf(g, str(networkx_file))
        elif networkx_format == "gml":
            networkx_file = networkx_stem.with_suffix(".gml")
            nx.write_gml(g, str(networkx_file))
        else:
            raise NotImplementedError()
        click.echo(networkx_file)
