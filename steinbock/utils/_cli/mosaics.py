from os import PathLike
from pathlib import Path
from typing import List, Sequence, Union

import click
import click_log
from skimage import measure

from ..._cli.utils import OrderedClickGroup, catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import mosaics


def _collect_tiff_files(
    img_files_or_dirs: Sequence[Union[str, PathLike]]
) -> List[Path]:
    img_files = []
    for img_file_or_dir in img_files_or_dirs:
        if Path(img_file_or_dir).is_file():
            img_files.append(Path(img_file_or_dir))
        else:
            img_files += sorted(Path(img_file_or_dir).rglob("*.tiff"))
    return img_files


@click.group(name="mosaics", cls=OrderedClickGroup, help="Mosaic tiling/stitching")
def mosaics_cmd_group():
    pass


@mosaics_cmd_group.command(name="tile", help="Extract tiles from images")
@click.argument("images", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--size",
    "tile_size",
    type=click.INT,
    required=True,
    help="Tile size (in pixels)",
)
@click.option(
    "--mmap/--no-mmap",
    "mmap",
    default=False,
    show_default=True,
    help="Use memory mapping for reading images",
)
@click.option(
    "-o",
    "tile_dir",
    type=click.Path(file_okay=False),
    required=True,
    help="Path to the tile output directory",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def tile_cmd(images, tile_size, mmap, tile_dir):
    img_files = _collect_tiff_files(images)
    Path(tile_dir).mkdir(exist_ok=True)
    for tile_file, tile in mosaics.try_extract_tiles_from_disk_to_disk(
        img_files, tile_dir, tile_size, mmap=mmap
    ):
        logger.info(tile_file)
        del tile


@mosaics_cmd_group.command(name="stitch", help="Combine tiles into images")
@click.argument("tiles", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--relabel/--no-relabel",
    "relabel",
    default=False,
    show_default=True,
    help="Relabel objects",
)
@click.option(
    "--mmap/--no-mmap",
    "mmap",
    default=False,
    show_default=True,
    help="Use memory mapping for writing images",
)
@click.option(
    "-o",
    "img_dir",
    type=click.Path(file_okay=False),
    required=True,
    help="Path to the tile output directory",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def stitch_cmd(tiles, relabel, mmap, img_dir):
    tile_files = _collect_tiff_files(tiles)
    Path(img_dir).mkdir(exist_ok=True)
    for img_file, img in mosaics.try_stitch_tiles_from_disk_to_disk(
        tile_files, img_dir, mmap=mmap
    ):
        if relabel:
            if img.ndim != 2:
                logger.warning(f"Failed to relabel image with shape {img.shape}")
                continue
            img[:] = measure.label(img)
            img.flush()
        logger.info(img_file)
        del img
