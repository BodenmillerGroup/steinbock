import logging
import re
from os import PathLike
from pathlib import Path
from typing import Generator, NamedTuple, Sequence, Tuple, Union

import numpy as np

from .. import io
from ._utils import SteinbockUtilsException

logger = logging.getLogger(__name__)


class SteinbockMosaicsUtilsException(SteinbockUtilsException):
    pass


def try_extract_tiles_from_disk_to_disk(
    img_files: Sequence[Union[str, PathLike]],
    tile_dir: Union[str, PathLike],
    tile_size: int,
    mmap: bool = False,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for img_file in img_files:
        try:
            if mmap:
                img = io.mmap_image(img_file)
            else:
                img = io.read_image(img_file, native_dtype=True)
            if img.shape[-1] % tile_size == 1 or img.shape[-2] % tile_size == 1:
                logger.warning(
                    "Chosen tile size yields UNSTITCHABLE tiles of 1 pixel "
                    f"width or height for image {img_file}"
                )
            for tile_x in range(0, img.shape[-1], tile_size):
                for tile_y in range(0, img.shape[-2], tile_size):
                    tile = img[
                        :,
                        tile_y : (tile_y + tile_size),
                        tile_x : (tile_x + tile_size),
                    ]
                    tile_file = Path(tile_dir) / (
                        f"{Path(img_file).stem}_tx{tile_x}_ty{tile_y}"
                        f"_tw{tile.shape[-1]}_th{tile.shape[-2]}.tiff"
                    )
                    io.write_image(tile, tile_file, ignore_dtype=True)
                    yield tile_file, tile
                    del tile
            del img
        except:
            logger.exception(f"Error extracting tiles: {img_file}")


def try_stitch_tiles_from_disk_to_disk(
    tile_files: Sequence[Union[str, PathLike]],
    img_dir: Union[str, PathLike],
    mmap: bool = False,
) -> Generator[Tuple[str, np.ndarray], None, None]:
    class TileInfo(NamedTuple):
        tile_file: Path
        x: int
        y: int
        width: int
        height: int

    tile_file_stem_pattern = re.compile(
        r"(?P<img_file_stem>.+)_tx(?P<x>\d+)_ty(?P<y>\d+)"
        r"_tw(?P<width>\d+)_th(?P<height>\d+)"
    )
    img_tile_infos = {}
    for tile_file in tile_files:
        m = tile_file_stem_pattern.fullmatch(tile_file.stem)
        if m is None:
            raise SteinbockMosaicsUtilsException(
                f"Malformed tile file name: {tile_file}"
            )
        img_file_stem = m.group("img_file_stem")
        tile_info = TileInfo(
            Path(tile_file),
            int(m.group("x")),
            int(m.group("y")),
            int(m.group("width")),
            int(m.group("height")),
        )
        if img_file_stem not in img_tile_infos:
            img_tile_infos[img_file_stem] = []
        img_tile_infos[img_file_stem].append(tile_info)
    for img_file_stem, tile_infos in img_tile_infos.items():
        img_file = Path(img_dir) / f"{img_file_stem}.tiff"
        try:
            tile = io.read_image(tile_infos[0].tile_file, native_dtype=True)
            img_shape = (
                tile.shape[0],
                max(ti.y + ti.height for ti in tile_infos),
                max(ti.x + ti.width for ti in tile_infos),
            )
            if mmap:
                img = io.mmap_image(
                    img_file, mode="r+", shape=img_shape, dtype=tile.dtype
                )
            else:
                img = np.zeros(img_shape, dtype=tile.dtype)
            for i, tile_info in enumerate(tile_infos):
                if i > 0:
                    tile = io.read_image(tile_info.tile_file, native_dtype=True)
                img[
                    :,
                    tile_info.y : tile_info.y + tile_info.height,
                    tile_info.x : tile_info.x + tile_info.width,
                ] = tile
                if mmap:
                    img.flush()
            if not mmap:
                io.write_image(img, img_file, ignore_dtype=True)
            yield img_file, img
            del img
        except:
            logger.exception(f"Error stitching tiles: {img_file}")
