from pathlib import Path

import click
import click_log
import numpy as np
import pandas as pd

from ... import io
from ..._cli.utils import OrderedClickGroup, catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import external


@click.group(
    name="external",
    cls=OrderedClickGroup,
    help="Preprocess external image data",
)
def external_cmd_group():
    pass


@external_cmd_group.command(
    name="panel", help="Create a panel from external image data"
)
@click.option(
    "--img",
    "ext_img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="external",
    show_default=True,
    help="Path to the external image file directory",
)
@click.option(
    "-o",
    "panel_file",
    type=click.Path(dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel output file",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def panel_cmd(ext_img_dir, panel_file):
    ext_img_files = external.list_image_files(ext_img_dir)
    panel = external.create_panel_from_image_files(ext_img_files)
    io.write_panel(panel, panel_file)
    logger.info(panel_file)


@external_cmd_group.command(name="images", help="Extract external images")
@click.option(
    "--img",
    "ext_img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="external",
    show_default=True,
    help="Path to the external image file directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the steinbock panel file",
)
@click.option(
    "--mmap/--no-mmap",
    "mmap",
    default=False,
    show_default=True,
    help="Use memory mapping for writing images",
)
@click.option(
    "--imgout",
    "img_dir",
    type=click.Path(file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image output directory",
)
@click.option(
    "--infoout",
    "image_info_file",
    type=click.Path(dir_okay=False),
    default="images.csv",
    show_default=True,
    help="Path to the image information output file",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def images_cmd(ext_img_dir, panel_file, mmap, img_dir, image_info_file):
    channel_indices = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if "channel" in panel:
            channel_indices = panel["channel"].astype(int).sub(1).tolist()
    ext_img_files = external.list_image_files(ext_img_dir)
    image_info_data = []
    Path(img_dir).mkdir(exist_ok=True)
    for ext_img_file, img in external.try_preprocess_images_from_disk(ext_img_files):
        # filter channels here rather than in try_preprocess_images_from_disk,
        # to avoid advanced indexing creating a copy of img (relevant for mmap)
        if channel_indices is not None:
            if max(channel_indices) > img.shape[0]:
                logger.warning(
                    f"Channel indices out of bounds for file {ext_img_file} "
                    f"with {img.shape[0]} channels"
                )
                continue
            cur_channel_indices = channel_indices
        else:
            cur_channel_indices = list(range(img.shape[0]))
        img_file = io._as_path_with_suffix(
            Path(img_dir) / Path(ext_img_file).name, ".tiff"
        )
        out_shape = list(img.shape)
        out_shape[0] = len(cur_channel_indices)
        out_shape = tuple(out_shape)
        if mmap:
            out = io.mmap_image(img_file, mode="r+", shape=out_shape, dtype=img.dtype)
        else:
            out = np.empty(out_shape, dtype=img.dtype)
        for i, channel_index in enumerate(cur_channel_indices):
            out[i, :, :] = img[channel_index, :, :]
            if mmap:
                out.flush()
        if not mmap:
            io.write_image(out, img_file)
        image_info_row = {
            "image": img_file.name,
            "width_px": img.shape[2],
            "height_px": img.shape[1],
            "num_channels": img.shape[0],
        }
        image_info_data.append(image_info_row)
        logger.info(img_file)
        del img
    image_info = pd.DataFrame(data=image_info_data)
    io.write_image_info(image_info, image_info_file)
