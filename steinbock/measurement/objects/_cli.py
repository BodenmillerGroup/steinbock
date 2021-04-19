import click
import numpy as np

from pathlib import Path

from steinbock.measurement.objects import objects
from steinbock.utils import cli, io

default_collect_data_dirs = [
    cli.default_intensities_dir,
    cli.default_regionprops_dir,
]

default_skimage_regionprops = [
    "area",
    "centroid",
    "major_axis_length",
    "minor_axis_length",
    "eccentricity",
]


@click.group(
    name="objects",
    cls=cli.OrderedClickGroup,
    help="Measure object properties",
)
def objects_cmd():
    pass


@objects_cmd.command(
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
    "aggr_function_name",
    type=click.STRING,
    default="mean",
    show_default=True,
    help="Numpy function for aggregating pixels",
)
@click.option(
    "--dest",
    "intensities_dir",
    type=click.Path(file_okay=False),
    default=cli.default_intensities_dir,
    show_default=True,
    help="Path to the object intensities output directory",
)
def intensities(
    img_dir,
    mask_dir,
    panel_file,
    aggr_function_name,
    intensities_dir,
):
    aggr_function = getattr(np, aggr_function_name)
    img_files = io.list_images(img_dir)
    panel = io.read_panel(panel_file)
    channel_names = panel[io.panel_name_col].tolist()
    intensities_dir = Path(intensities_dir)
    intensities_dir.mkdir(exist_ok=True)
    for img_file, mask_file, intensities in objects.measure_intensities(
        img_files,
        io.list_masks(mask_dir),
        channel_names,
        aggr_function,
    ):
        intensities_file = io.write_data(
            intensities,
            intensities_dir / img_file.stem,
        )
        click.echo(intensities_file)
        del intensities


@objects_cmd.command(
    help="Measure object region properties",
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
@click.argument(
    "skimage_regionprops",
    nargs=-1,
    type=click.STRING,
)
@click.option(
    "--dest",
    "regionprops_dir",
    type=click.Path(file_okay=False),
    default=cli.default_regionprops_dir,
    show_default=True,
    help="Path to the object region properties output directory",
)
def regionprops(
    img_dir,
    mask_dir,
    panel_file,
    skimage_regionprops,
    regionprops_dir,
):
    img_files = io.list_images(img_dir)
    panel = io.read_panel(panel_file)
    channel_names = panel[io.panel_name_col].tolist()
    regionprops_dir = Path(regionprops_dir)
    regionprops_dir.mkdir(exist_ok=True)
    if not skimage_regionprops:
        skimage_regionprops = default_skimage_regionprops
    for img_file, mask_file, regionprops in objects.measure_regionprops(
        img_files,
        io.list_masks(mask_dir),
        channel_names,
        skimage_regionprops,
    ):
        regionprops_file = regionprops_dir / img_file.stem
        regionprops_file = io.write_data(regionprops, regionprops_file)
        click.echo(regionprops_file)
        del regionprops


@objects_cmd.command(
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
    combined_data = objects.combine(data_dirs)
    io.write_data(combined_data, combined_data_file, combined=True)
