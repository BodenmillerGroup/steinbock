import click

from pathlib import Path

from steinbock.measurement.cells.cells import (
    measure_cell_intensities,
    combine_cell_data,
)
from steinbock.utils import cli, io


@click.group(
    cls=cli.OrderedClickGroup,
    help="",  # TODO
)
def cells():
    pass


@cells.command(
    help="Measure mean cell intensities",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image .tiff directory",
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask .tiff directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default=cli.default_panel_file,
    show_default=True,
    help="Path to the panel .csv file",
)
@click.option(
    "--dest",
    "cell_intensities_dir",
    type=click.Path(file_okay=False),
    default=cli.default_cell_intensities_dir,
    show_default=True,
    help="Path to the cell intensities output directory",
)
def intensities(img_dir, mask_dir, panel_file, cell_intensities_dir):
    img_files = sorted(Path(img_dir).glob("*.tiff"))
    mask_files = sorted(Path(mask_dir).glob("*.tiff"))
    panel = io.read_panel(panel_file)
    channel_names = panel[io.panel_name_col].tolist()
    cell_intensities_dir = Path(cell_intensities_dir)
    cell_intensities_dir.mkdir(exist_ok=True)
    it = measure_cell_intensities(img_files, mask_files, channel_names)
    with click.progressbar(it, length=len(img_files)) as pbar:
        for img_file, mask_file, cell_intensities in pbar:
            io.write_cell_data(
                cell_intensities,
                cell_intensities_dir / img_file.with_suffix(".csv").name,
            )


@cells.command(
    help="Combine cell data into a single file",
)
@click.option(
    "--data",
    "cell_data_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_cell_intensities_dir,
    show_default=True,
    help="Path to the cell data .csv directory",
)
@click.option(
    "--dest",
    "combined_cell_data_file",
    type=click.Path(dir_okay=False),
    default=cli.default_combined_cell_data_file,
    show_default=True,
    help="Path to the combined cell data output file",
)
def collect(cell_data_dir, combined_cell_data_file):
    cell_data_files = sorted(Path(cell_data_dir).glob("*.csv"))
    combined_cell_data = combine_cell_data(
        cell_data_files,
    )
    combined_cell_data.to_csv(combined_cell_data_file)
