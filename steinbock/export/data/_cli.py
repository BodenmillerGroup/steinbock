import click

from pathlib import Path

from steinbock import cli
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
    help="Collect object data into a Comma-Separated Values (CSV) file",
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
    help="Path to the combined object data CSV file",
)
@check_version
def csv_cmd(data_dirs, combined_data_csv_file):
    if not data_dirs:
        data_dirs = filter(lambda x: Path(x).exists(), default_data_dirs)
    combined_data = data.collect_data_from_disk(data_dirs)
    data.write_combined_data_csv(
        combined_data,
        combined_data_csv_file,
        copy=False,
    )


@data_cmd_group.command(
    name="fcs",
    help="Collect object data into a Flow Cytometry Standard (FCS) file",
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
    help="Path to the combined object data FCS file",
)
@check_version
def fcs_cmd(data_dirs, combined_data_fcs_file):
    if not data_dirs:
        data_dirs = filter(lambda x: Path(x).exists(), default_data_dirs)
    combined_data = data.collect_data_from_disk(data_dirs)
    data.write_combined_data_fcs(combined_data, combined_data_fcs_file)
