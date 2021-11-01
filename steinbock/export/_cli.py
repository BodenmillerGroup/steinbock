import click
import networkx as nx
import numpy as np

from fcswrite import write_fcs
from pathlib import Path
from tifffile import imwrite
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
    channel_names = [
        f"{channel_id}_{channel_name}"
        for channel_id, channel_name in zip(
            panel["channel"].values, panel["name"].values
        )
    ]
    Path(ome_dir).mkdir(exist_ok=True)
    for img_file in io.list_image_files(img_dir):
        img = io.read_image(img_file)
        ome_file = io._as_path_with_suffix(
            Path(ome_dir) / img_file.name, ".ome.tiff"
        )
        to_tiff(img, ome_file, channel_names=channel_names)
        click.echo(ome_file.name)
        del img


@export_cmd_group.command(
    name="histocat", help="Export images to histoCAT for MATLAB"
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask directory",
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
    "histocat_dir",
    type=click.Path(file_okay=False),
    default="histocat",
    show_default=True,
    help="Path to the histoCAT export directory",
)
@check_steinbock_version
def histocat_cmd(img_dir, mask_dir, panel_file, histocat_dir):
    panel = io.read_panel(panel_file)
    channel_names = [
        f"{channel_id}_{channel_name}"
        for channel_id, channel_name in zip(
            panel["channel"].values, panel["name"].values
        )
    ]
    img_files = io.list_image_files(img_dir)
    mask_files = None
    if Path(mask_dir).exists():
        mask_files = io.list_mask_files(mask_dir, base_files=img_files)
    Path(histocat_dir).mkdir(exist_ok=True)
    for i, img_file in enumerate(img_files):
        img = io.read_image(img_file, ignore_dtype=True)
        histocat_img_dir = Path(histocat_dir) / img_file.stem
        histocat_img_dir.mkdir(exist_ok=True)
        for channel_name, channel_img in zip(channel_names, img):
            imwrite(
                histocat_img_dir / f"{channel_name}.tiff",
                data=io._to_dtype(channel_img, np.float32),
            )
        mask = None
        if mask_files is not None:
            mask = io.read_mask(mask_files[i])
            imwrite(
                histocat_img_dir / f"{img_file.stem}_mask.tiff",
                data=io._to_dtype(mask, np.uint16),
            )
        click.echo(img_file.name)
        del img, mask


@export_cmd_group.command(
    name="csv", help="Merge and export object data to CSV"
)
@click.argument(
    "data_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "--concat/--no-concat",
    "concatenate",
    default=False,
    show_default=True,
    help="Concatenate all files into a single file",
)
@click.option(
    "-o",
    "csv_file_or_dir",
    type=click.Path(),
    default="csv",
    show_default=True,
    help="Path to the CSV output file or directory",
)
@check_steinbock_version
def csv_cmd(data_dirs, concatenate, csv_file_or_dir):
    if not data_dirs:
        return  # empty variadic argument, gracefully degrade into noop
    if concatenate and Path(csv_file_or_dir).is_dir():
        pass  # TODO
    elif not concatenate and Path(csv_file_or_dir).is_file():
        pass  # TODO
    first_data_files = io.list_data_files(data_dirs[0])
    data_file_lists = [first_data_files]
    for data_dir in data_dirs[1:]:
        data_files = io.list_data_files(data_dir, base_files=first_data_files)
        data_file_lists.append(data_files)
    if concatenate:
        Path(csv_file_or_dir).mkdir(exist_ok=True)
    gen = data.try_convert_to_dataframe_from_disk(
        *data_file_lists, concatenate=concatenate
    )
    try:
        while True:
            img_file_name, data_files, df = next(gen)
            if concatenate:
                click.echo(img_file_name)
            else:
                csv_file = io._as_path_with_suffix(
                    Path(csv_file_or_dir) / img_file_name, ".csv"
                )
                df.reset_index(inplace=True)
                df.to_csv(csv_file, index=False)
                click.echo(csv_file.name)
                del df
    except StopIteration as e:
        if concatenate:
            df = e.value
            df.reset_index(inplace=True)
            df.to_csv(csv_file_or_dir, index=False)


@export_cmd_group.command(
    name="fcs", help="Merge and export object data to FCS"
)
@click.argument(
    "data_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "--concat/--no-concat",
    "concatenate",
    default=False,
    show_default=True,
    help="Concatenate all files into a single file",
)
@click.option(
    "-o",
    "fcs_file_or_dir",
    type=click.Path(),
    default="fcs",
    show_default=True,
    help="Path to the FCS output file or directory",
)
@check_steinbock_version
def fcs_cmd(data_dirs, concatenate, fcs_file_or_dir):
    if not data_dirs:
        return  # empty variadic argument, gracefully degrade into noop
    if concatenate and Path(fcs_file_or_dir).is_dir():
        pass  # TODO
    elif not concatenate and Path(fcs_file_or_dir).is_file():
        pass  # TODO
    first_data_files = io.list_data_files(data_dirs[0])
    data_file_lists = [first_data_files]
    for data_dir in data_dirs[1:]:
        data_files = io.list_data_files(data_dir, base_files=first_data_files)
        data_file_lists.append(data_files)
    if concatenate:
        Path(fcs_file_or_dir).mkdir(exist_ok=True)
    gen = data.try_convert_to_dataframe_from_disk(
        *data_file_lists, concatenate=concatenate
    )
    try:
        while True:
            img_file_name, data_files, df = next(gen)
            if concatenate:
                click.echo(img_file_name)
            else:
                fcs_file = io._as_path_with_suffix(
                    Path(fcs_file_or_dir) / img_file_name, ".fcs"
                )
                df.reset_index(inplace=True)
                write_fcs(fcs_file, df.columns.values, df.values)
                click.echo(fcs_file.name)
                del df
    except StopIteration as e:
        if concatenate:
            df = e.value
            df.reset_index(inplace=True)
            write_fcs(fcs_file_or_dir, df.columns.values, df.values)


@export_cmd_group.command(
    name="anndata", help="Merge and export object data to AnnData"
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
    "--concat/--no-concat",
    "concatenate",
    default=False,
    show_default=True,
    help="Concatenate all files into a single file",
)
@click.option(
    "-o",
    "adata_file_or_dir",
    type=click.Path(),
    default="anndata",
    show_default=True,
    help="Path to the AnnData output file or directory",
)
@click.option(
    "--format",
    "adata_format",
    type=click.Choice(["h5ad", "loom", "zarr"], case_sensitive=False),
    default="h5ad",
    show_default=True,
    help="AnnData file format to use",
)
@check_steinbock_version
def anndata_cmd(
    x_data_dir, obs_data_dirs, concatenate, adata_file_or_dir, adata_format
):
    if adata_format.lower() == "h5ad":

        def write_adata(adata, adata_file, keep_suffix=False):
            suffix = Path(adata_file).suffix if keep_suffix else ".h5ad"
            adata_file = io._as_path_with_suffix(adata_file, suffix)
            adata.write_h5ad(adata_file)
            return adata_file

    elif adata_format.lower() == "loom":

        def write_adata(adata, adata_file, keep_suffix=False):
            suffix = Path(adata_file).suffix if keep_suffix else ".loom"
            adata_file = io._as_path_with_suffix(adata_file, suffix)
            adata.write_loom(adata_file)
            return adata_file

    elif adata_format.lower() == "zarr":

        def write_adata(adata, adata_file, keep_suffix=False):
            suffix = Path(adata_file).suffix if keep_suffix else ".zarr"
            adata_file = io._as_path_with_suffix(adata_file, suffix)
            adata.write_zarr(adata_file)
            return adata_file

    else:
        raise NotImplementedError()

    if concatenate and Path(adata_file_or_dir).is_dir():
        pass  # TODO
    elif not concatenate and Path(adata_file_or_dir).is_file():
        pass  # TODO
    x_data_files = io.list_data_files(x_data_dir)
    obs_data_file_lists = [
        io.list_data_files(obs_data_dir, base_files=x_data_files)
        for obs_data_dir in obs_data_dirs
    ]
    if concatenate:
        Path(adata_file_or_dir).mkdir(exist_ok=True)
    gen = data.try_convert_to_anndata_from_disk(
        x_data_files, *obs_data_file_lists, concatenate=concatenate
    )
    try:
        while True:
            img_file_name, x_data_file, obs_data_files, adata = next(gen)
            if concatenate:
                click.echo(img_file_name)
            else:
                adata_file = io._as_path_with_suffix(
                    Path(adata_file_or_dir) / img_file_name, ".adata"
                )
                adata_file = write_adata(adata, adata_file)
                click.echo(adata_file.name)
                del adata
    except StopIteration as e:
        if concatenate:
            adata = e.value
            write_adata(adata, adata_file_or_dir, keep_suffix=True)


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
