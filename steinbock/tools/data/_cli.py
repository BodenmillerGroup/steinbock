import click

from pathlib import Path

from steinbock.tools.data import data
from steinbock.utils import cli, io

default_collect_data_dirs = [
    cli.default_intensities_dir,
    cli.default_regionprops_dir,
]


@click.group(
    name="data",
    cls=cli.OrderedClickGroup,
    help="Data processing tools",
)
def data_cmd():
    pass


@data_cmd.command(
    help="Combine object data into a single file",
)
@click.argument(
    "data_dirs",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--dest",
    "combined_data_file",
    type=click.Path(dir_okay=False),
    default=cli.default_combined_data_file,
    show_default=True,
    help="Path to the combined object data output file",
)
def collect(data_dirs, combined_data_file):
    if not data_dirs:
        data_dirs = [
            data_dir
            for data_dir in default_collect_data_dirs
            if Path(data_dir).exists()
        ]
    combined_data = data.collect_data(data_dirs)
    io.write_data(combined_data, combined_data_file, combined=True)
