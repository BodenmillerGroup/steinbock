import logging
import numpy as np

from os import PathLike
from pathlib import Path
from typing import Dict, Generator, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)


def try_extract_tiles_from_disk(
    img_files: Sequence[Union[str, PathLike]], tile_size: int
) -> Generator[Tuple[Path, int, int, int, int, np.ndarray], None, None]:
    for img_file in img_files:
        try:
            img = io.read_image(img_file, ignore_dtype=True)
            for x in range(0, img.shape[2], tile_size):
                for y in range(0, img.shape[1], tile_size):
                    tile = img[:, y : (y + tile_size), x : (x + tile_size)]
                    yield Path(img_file), x, y, tile_size, tile_size, tile
                    del tile
            del img
        except:
            _logger.exception(f"Error extracting tiles: {img_file}")


def try_stitch_tiles_from_disk(
    tile_info_groups: Dict[
        str, Sequence[Tuple[Union[str, PathLike], int, int, int, int]]
    ]
) -> Generator[Tuple[str, np.ndarray], None, None]:
    for img_stem_name, tile_info in tile_info_groups.items():
        try:
            first_tile = io.read_image(tile_info[0][0], ignore_dtype=True)
            img_width = max(x + w for _, x, y, w, h in tile_info)
            img_height = max(y + h for _, x, y, w, h in tile_info)
            img = np.zeros(
                (first_tile.shape[0], img_height, img_width),
                dtype=first_tile.dtype,
            )
            for tile_file, x, y, w, h in tile_info:
                img[:, y : (y + h), x : (x + w)] = io.read_image(
                    tile_file, ignore_dtype=True
                )
            yield img_stem_name, img
            del img
        except:
            _logger.exception(f"Error stitching tiles: {img_stem_name}")
