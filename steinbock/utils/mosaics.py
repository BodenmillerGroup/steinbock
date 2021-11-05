import logging
import numpy as np

from os import PathLike
from pathlib import Path
from typing import Dict, Generator, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)

TileInfo = Tuple[Union[str, PathLike], int, int, int, int]


def try_extract_tiles_from_disk(
    img_files: Sequence[Union[str, PathLike]], tile_size: int
) -> Generator[Tuple[Path, int, int, np.ndarray], None, None]:
    for img_file in img_files:
        try:
            img = io.read_image(img_file, native_dtype=True)
            for tile_x in range(0, img.shape[2], tile_size):
                for tile_y in range(0, img.shape[1], tile_size):
                    tile = img[
                        :,
                        tile_y : (tile_y + tile_size),
                        tile_x : (tile_x + tile_size),
                    ]
                    yield Path(img_file), tile_x, tile_y, tile
                    del tile
            del img
        except:
            _logger.exception(f"Error extracting tiles: {img_file}")


def try_stitch_tiles_from_disk(
    img_tile_infos: Dict[str, Sequence[TileInfo]]
) -> Generator[Tuple[str, np.ndarray], None, None]:
    for img_stem_name, tile_infos in img_tile_infos.items():
        try:
            tile_file, tile_x, tile_y, tile_width, tile_height = tile_infos[0]
            tile = io.read_image(tile_file, native_dtype=True)
            img = np.zeros(
                (
                    tile.shape[0],
                    max(x + w for _, x, y, w, h in tile_infos),
                    max(y + h for _, x, y, w, h in tile_infos),
                ),
                dtype=tile.dtype,
            )
            img[
                :,
                tile_y : (tile_y + tile_height),
                tile_x : (tile_x + tile_width),
            ] = tile
            for (
                tile_file,
                tile_x,
                tile_y,
                tile_width,
                tile_height,
            ) in tile_infos[1:]:
                img[
                    :,
                    tile_y : (tile_y + tile_height),
                    tile_x : (tile_x + tile_width),
                ] = io.read_image(tile_file, native_dtype=True)
            yield img_stem_name, img
            del img
        except:
            _logger.exception(f"Error stitching tiles: {img_stem_name}")
