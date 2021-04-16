import click
import numpy as np

from pathlib import Path

from steinbock.measurement.cells import cells
from steinbock.utils import cli, io

default_collect_cell_data_dirs = [
    cli.default_cell_intensities_dir,
    cli.default_cell_regionprops_dir,
]

default_skimage_regionprops = [
    "area",
    "centroid",
    "major_axis_length",
    "minor_axis_length",
    "eccentricity",
]


@click.group(
    name="cells",
    cls=cli.OrderedClickGroup,
    help="Measure cell properties",
)
def cells_cmd():
    pass


@cells_cmd.command(
    help="Measure cell intensities",
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
    "cell_intensities_dir",
    type=click.Path(file_okay=False),
    default=cli.default_cell_intensities_dir,
    show_default=True,
    help="Path to the cell intensities output directory",
)
def intensities(
    img_dir,
    mask_dir,
    panel_file,
    aggr_function_name,
    cell_intensities_dir,
):
    aggr_function = getattr(np, aggr_function_name)
    img_files = io.list_images(img_dir)
    panel = io.read_panel(panel_file)
    channel_names = panel[io.panel_name_col].tolist()
    cell_intensities_dir = Path(cell_intensities_dir)
    cell_intensities_dir.mkdir(exist_ok=True)
    for img_file, mask_file, cell_intensities in cells.measure_intensities(
        img_files,
        io.list_masks(mask_dir),
        channel_names,
        aggr_function,
    ):
        cell_intensities_file = cell_intensities_dir / img_file.stem
        cell_intensities_file = io.write_cell_data(
            cell_intensities,
            cell_intensities_file,
        )
        click.echo(cell_intensities_file)
        del cell_intensities


@cells_cmd.command(
    help="Measure cell region properties",
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
    "cell_regionprops_dir",
    type=click.Path(file_okay=False),
    default=cli.default_cell_regionprops_dir,
    show_default=True,
    help="Path to the cell region properties output directory",
)
def regionprops(
    img_dir,
    mask_dir,
    panel_file,
    skimage_regionprops,
    cell_regionprops_dir,
):
    img_files = io.list_images(img_dir)
    panel = io.read_panel(panel_file)
    channel_names = panel[io.panel_name_col].tolist()
    cell_regionprops_dir = Path(cell_regionprops_dir)
    cell_regionprops_dir.mkdir(exist_ok=True)
    if not skimage_regionprops:
        skimage_regionprops = default_skimage_regionprops
    for img_file, mask_file, cell_regionprops in cells.measure_regionprops(
        img_files,
        io.list_masks(mask_dir),
        channel_names,
        skimage_regionprops,
    ):
        cell_regionprops_file = cell_regionprops_dir / img_file.stem
        cell_regionprops_file = io.write_cell_data(
            cell_regionprops,
            cell_regionprops_file,
        )
        click.echo(cell_regionprops_file)
        del cell_regionprops


@cells_cmd.command(
    help="Combine cell data into a single file",
)
@click.argument(
    "cell_data_dirs",
    nargs=-1,
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "--dest",
    "combined_cell_data_file",
    type=click.Path(dir_okay=False),
    default=cli.default_combined_cell_data_file,
    show_default=True,
    help="Path to the combined cell data output file",
)
def collect(cell_data_dirs, combined_cell_data_file):
    if not cell_data_dirs:
        cell_data_dirs = [
            cell_data_dir
            for cell_data_dir in default_collect_cell_data_dirs
            if Path(cell_data_dir).exists()
        ]
    combined_cell_data = cells.combine_cell_data(cell_data_dirs)
    combined_cell_data.to_csv(combined_cell_data_file)
