import click
import pandas as pd
import sys

from anndata import concat as anndata_concat
from fcswrite import write_fcs
from pathlib import Path

from steinbock import io
from steinbock._env import check_steinbock_version
from steinbock.export import data


@click.command(name="csv", help="Merge and export object data to CSV")
@click.argument(
    "data_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "--concat/--no-concat",
    "concatenate",
    default=True,
    show_default=True,
    help="Concatenate all files into a single file",
)
@click.option(
    "-o",
    "csv_file_or_dir",
    type=click.Path(),
    default="objects.csv",
    show_default=True,
    help="Path to the CSV output file or directory",
)
@check_steinbock_version
def csv_cmd(data_dirs, concatenate, csv_file_or_dir):
    if not data_dirs:
        return  # empty variadic argument, gracefully degrade into noop
    if concatenate and Path(csv_file_or_dir).is_dir():
        return click.echo(
            "ERROR: Specify a single output file when concatenating",
            file=sys.stderr,
        )
    elif not concatenate and Path(csv_file_or_dir).is_file():
        return click.echo("ERROR: Output directory is a file", file=sys.stderr)
    first_data_files = io.list_data_files(data_dirs[0])
    data_file_lists = [first_data_files]
    for data_dir in data_dirs[1:]:
        data_files = io.list_data_files(data_dir, base_files=first_data_files)
        data_file_lists.append(data_files)
    if not concatenate:
        Path(csv_file_or_dir).mkdir(exist_ok=True)
    for i, (img_file_name, data_files, df) in enumerate(
        data.try_convert_to_dataframe_from_disk(*data_file_lists)
    ):
        df.reset_index(inplace=True)
        if concatenate:
            df.insert(0, "Image", img_file_name)
            if i == 0:
                df.to_csv(csv_file_or_dir, index=False)
            else:
                df.to_csv(csv_file_or_dir, header=False, index=False, mode="a")
            click.echo(img_file_name)
        else:
            csv_file = io._as_path_with_suffix(
                Path(csv_file_or_dir) / img_file_name, ".csv"
            )
            df.to_csv(csv_file, index=False)
            click.echo(csv_file.name)
        del df


@click.command(name="fcs", help="Merge and export object data to FCS")
@click.argument(
    "data_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False)
)
@click.option(
    "--concat/--no-concat",
    "concatenate",
    default=True,
    show_default=True,
    help="Concatenate all files into a single file",
)
@click.option(
    "-o",
    "fcs_file_or_dir",
    type=click.Path(),
    default="objects.fcs",
    show_default=True,
    help="Path to the FCS output file or directory",
)
@check_steinbock_version
def fcs_cmd(data_dirs, concatenate, fcs_file_or_dir):
    if not data_dirs:
        return  # empty variadic argument, gracefully degrade into noop
    if concatenate and Path(fcs_file_or_dir).is_dir():
        return click.echo(
            "ERROR: Specify a single output file when concatenating",
            file=sys.stderr,
        )
    elif not concatenate and Path(fcs_file_or_dir).is_file():
        return click.echo("ERROR: Output directory is a file", file=sys.stderr)
    first_data_files = io.list_data_files(data_dirs[0])
    data_file_lists = [first_data_files]
    for data_dir in data_dirs[1:]:
        data_files = io.list_data_files(data_dir, base_files=first_data_files)
        data_file_lists.append(data_files)
    if concatenate:
        click.echo(
            "WARNING: The fcswrite package currently does not support on-disk "
            "concatenation; all files will be loaded into memory"
        )
    else:
        Path(fcs_file_or_dir).mkdir(exist_ok=True)
    dfs = []
    for (
        img_file_name,
        data_files,
        df,
    ) in data.try_convert_to_dataframe_from_disk(*data_file_lists):
        if concatenate:
            click.echo(img_file_name)
            dfs.append(df)
        else:
            fcs_file = io._as_path_with_suffix(
                Path(fcs_file_or_dir) / img_file_name, ".fcs"
            )
            write_fcs(fcs_file, df.columns.values, df.values)
            click.echo(fcs_file.name)
            del df
    if concatenate:
        df = pd.concat(dfs, ignore_index=True, copy=False)
        write_fcs(fcs_file_or_dir, df.columns.values, df.values)


@click.command(name="anndata", help="Merge and export object data to AnnData")
@click.option(
    "--intensities",
    "intensities_dir",
    required=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path to the intensities directory",
)
@click.option(
    "--data",
    "data_dirs",
    multiple=True,
    type=click.Path(exists=True, file_okay=False),
    help="Path to the object data directory",
)
@click.option(
    "--neighbors",
    "neighbors_dir",
    type=click.Path(exists=True, file_okay=False),
    help="Path to the neighbors directory",
)
# @click.option(
#     "--panel",
#     "panel_file",
#     type=click.Path(dir_okay=False),
#     default="panel.csv",
#     show_default=True,
#     help="Path to the panel file",
# )
# @click.option(
#     "--info",
#     "image_info_file",
#     type=click.Path(dir_okay=False),
#     default="images.csv",
#     show_default=True,
#     help="Path to the image information file",
# )
@click.option(
    "--concat/--no-concat",
    "concatenate",
    default=True,
    show_default=True,
    help="Concatenate all files into a single file",
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
    "anndata_file_or_dir",
    type=click.Path(),
    default="objects.h5ad",
    show_default=True,
    help="Path to the AnnData output file or directory",
)
@check_steinbock_version
def anndata_cmd(
    intensities_dir,
    data_dirs,
    neighbors_dir,
    # panel_file,
    # image_info_file,
    concatenate,
    anndata_format,
    anndata_file_or_dir,
):
    if anndata_format == "h5ad":

        def write_anndata(adata, anndata_file, keep_suffix=False):
            suffix = Path(anndata_file).suffix if keep_suffix else ".h5ad"
            anndata_file = io._as_path_with_suffix(anndata_file, suffix)
            adata.write_h5ad(anndata_file)
            return anndata_file

    elif anndata_format == "loom":

        def write_anndata(adata, anndata_file, keep_suffix=False):
            suffix = Path(anndata_file).suffix if keep_suffix else ".loom"
            anndata_file = io._as_path_with_suffix(anndata_file, suffix)
            adata.write_loom(anndata_file)
            return anndata_file

    elif anndata_format == "zarr":

        def write_anndata(adata, anndata_file, keep_suffix=False):
            suffix = Path(anndata_file).suffix if keep_suffix else ".zarr"
            anndata_file = io._as_path_with_suffix(anndata_file, suffix)
            adata.write_zarr(anndata_file)
            return anndata_file

    else:
        raise NotImplementedError()

    intensities_files = io.list_data_files(intensities_dir)
    data_file_lists = [
        io.list_data_files(data_dir, base_files=intensities_files)
        for data_dir in data_dirs
        if Path(data_dir).is_dir()
    ]
    neighbors_files = None
    if neighbors_dir is not None and Path(neighbors_dir).is_dir():
        neighbors_files = io.list_neighbors_files(
            neighbors_dir, base_files=intensities_files
        )
    # panel = None
    # if panel_file is not None and Path(panel_file).is_file():
    #     panel = io.read_panel(panel_file)
    # image_info = None
    # if image_info_file is not None and Path(image_info_file).is_file():
    #     image_info = io.read_image_info(image_info_file)
    if concatenate and Path(anndata_file_or_dir).is_dir():
        return click.echo(
            "ERROR: Specify a single output file when concatenating",
            file=sys.stderr,
        )
    elif not concatenate and Path(anndata_file_or_dir).is_file():
        return click.echo("ERROR: Output directory is a file", file=sys.stderr)
    if concatenate:
        click.echo(
            "WARNING: The anndata package currently does not support on-disk "
            "concatenation (https://github.com/theislab/anndata/issues/312); "
            "all files will be loaded into memory"
        )
    else:
        Path(anndata_file_or_dir).mkdir(exist_ok=True)
    adatas = {}
    for (
        img_file_name,
        intensities_file,
        data_files,
        neighbors_file,
        adata,
    ) in data.try_convert_to_anndata_from_disk(
        intensities_files,
        *data_file_lists,
        neighbors_files=neighbors_files,
        # panel=panel,
        # image_info=image_info,
    ):
        if concatenate:
            adatas[img_file_name] = adata
            click.echo(img_file_name)
        else:
            anndata_file = io._as_path_with_suffix(
                Path(anndata_file_or_dir) / img_file_name, ".adata"
            )
            anndata_file = write_anndata(adata, anndata_file)
            click.echo(anndata_file.name)
            del adata
    if concatenate:
        adata = anndata_concat(
            adatas, merge="first", label="Image", index_unique=" in "
        )
        obs_cols = list(adata.obs.columns)
        obs_cols.insert(0, obs_cols.pop(obs_cols.index("Image")))
        adata.obs = adata.obs.loc[:, obs_cols]
        write_anndata(adata, anndata_file_or_dir, keep_suffix=True)
