import click
import numpy as np

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.measurement.intensities import intensities


@click.command(
    name="intensities",
    help="Measure object intensities",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default=cli.default_panel_file,
    show_default=True,
    help="Path to the panel file",
)
@click.option(
    "--aggr",
    "aggr_func_name",
    type=click.STRING,
    default="mean",
    show_default=True,
    help="Numpy function for aggregating cell pixels",
)
@click.option(
    "--dest",
    "intensities_dir",
    type=click.Path(file_okay=False),
    default=cli.default_intensities_dir,
    show_default=True,
    help="Path to the object intensities output directory",
)
@check_version
def intensities_cmd(
    img_dir,
    mask_dir,
    panel_file,
    aggr_func_name,
    intensities_dir,
):
    panel = io.read_panel(panel_file)
    aggr_func = getattr(np, aggr_func_name)
    intensities_dir = Path(intensities_dir)
    intensities_dir.mkdir(exist_ok=True)
    for img_file, mask_file, df in intensities.measure_intensities_from_disk(
        io.list_img_files(img_dir),
        io.list_mask_files(mask_dir),
        panel[io.channel_name_col].tolist(),
        aggr_func,
    ):
        intensities_file = intensities_dir / img_file.stem
        intensities_file = io.write_data(df, intensities_file, copy=False)
        click.echo(intensities_file)
        del df
