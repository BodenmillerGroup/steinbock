from pathlib import Path

import click
import click_log

from .. import io
from .._steinbock import SteinbockException
from .._steinbock import logger as steinbock_logger
from ..visualization import view
from .utils import catch_exception


@click.command(name="view", help="View image using napari GUI")
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--masks",
    "mask_dirs",
    multiple=True,
    type=click.Path(exists=True, file_okay=False),
    default=["masks"],
    show_default=True,
    help="Path(s) to the mask directory",
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
    "--pixelsize",
    "pixel_size_um",
    type=click.FLOAT,
    default=1.0,
    show_default=True,
    help="Pixel size in micrometers",
)
@click.argument("img_file_name", type=click.STRING)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def view_cmd(img_dir, mask_dirs, panel_file, pixel_size_um, img_file_name):
    img = io.read_image(Path(img_dir) / img_file_name, native_dtype=True)
    masks = None
    if len(mask_dirs) > 0:
        masks = {
            f"Mask ({Path(mask_dir).name})": io.read_mask(
                Path(mask_dir) / img_file_name, native_dtype=True
            )
            for mask_dir in mask_dirs
        }
    channel_names = None
    if Path(panel_file).is_file():
        panel = io.read_panel(panel_file)
        if "channel" in panel:
            channel_names = panel["name"].tolist()
    view(img, masks=masks, channel_names=channel_names, pixel_size_um=pixel_size_um)
