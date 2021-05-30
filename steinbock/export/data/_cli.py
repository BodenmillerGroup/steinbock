import click

from fcswrite import write_fcs
from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.export.data import data

default_data_dirs = [
    cli.default_intensities_dir,
    cli.default_regionprops_dir,
]


@click.group(
    name="data",
    cls=cli.OrderedClickGroup,
    help="Object data export",
)
def data_cmd_group():
    pass


@data_cmd_group.command(
    name="csv",
    help="Collect object data into a Comma-Separated Values (.csv) file",
)
@click.argument(
    "data_dirs",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--dest",
    "combined_data_csv_file",
    type=click.Path(dir_okay=False),
    default=cli.default_combined_data_csv_file,
    show_default=True,
    help="Path to the combined object data .csv file",
)
@check_version
def csv_cmd(data_dirs, combined_data_csv_file):
    if not data_dirs:
        data_dirs = filter(lambda x: Path(x).exists(), default_data_dirs)
    combined_data = data.collect_data_from_disk(data_dirs)
    combined_data.reset_index(inplace=True)
    combined_data.to_csv(combined_data_csv_file, index=False)


@data_cmd_group.command(
    name="fcs",
    help="Collect object data into a Flow Cytometry Standard (.fcs) file",
)
@click.argument(
    "data_dirs",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--dest",
    "combined_data_fcs_file",
    type=click.Path(dir_okay=False),
    default=cli.default_combined_data_fcs_file,
    show_default=True,
    help="Path to the combined object data .fcs file",
)
@check_version
def fcs_cmd(data_dirs, combined_data_fcs_file):
    if not data_dirs:
        data_dirs = filter(lambda x: Path(x).exists(), default_data_dirs)
    combined_data = data.collect_data_from_disk(data_dirs)
    write_fcs(
        combined_data_fcs_file,
        combined_data.columns.names,
        combined_data.values
    )


@data_cmd_group.command(
    name="anndata",
    help="Export object data as AnnData HDF5 (.h5ad) files",
)
@click.option(
    "--intensities",
    "intensities_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_intensities_dir,
    show_default=True,
    help="Path to the object intensities directory",
)
@click.option(
    "--regionprops",
    "regionprops_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_regionprops_dir,
    show_default=True,
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
    default=cli.default_anndata_dir,
    show_default=True,
    help="Path to the AnnData output directory",
)
def anndata_cmd(intensities_dir, regionprops_dir, anndata_dir, anndata_format):
    intensities_files = io.list_data_files(intensities_dir)
    regionprops_files = None
    if regionprops_dir is not None and Path(regionprops_dir).exists():
        regionprops_files = io.list_data_files(regionprops_dir)
    anndata_dir = Path(anndata_dir)
    anndata_dir.mkdir(exist_ok=True)
    for intensities_file, regionprops_file, ad in data.to_anndata_from_disk(
        intensities_files,
        regionprops_files
    ):
        ad_file = anndata_dir / intensities_file.name
        if anndata_format.lower() == "h5ad":
            ad_file = ad_file.with_suffix(".h5ad")
            ad.write_h5ad(ad_file)
        elif anndata_format.lower() == "loom":
            ad_file = ad_file.with_suffix(".loom")
            ad.write_loom(ad_file)
        elif anndata_format.lower() == "zarr":
            ad_file = ad_file.with_suffix(".zarr")
            ad.write_zarr(ad_file)
        click.echo(ad_file)
