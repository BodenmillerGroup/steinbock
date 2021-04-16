import numpy as np

from os import PathLike
from pathlib import Path
from typing import Dict, Generator, Sequence, Tuple, Union

from steinbock.utils import io

TileInfo = Tuple[Union[str, PathLike], int, int, int, int]


def extract_tiles(
    img_files: Sequence[Union[str, PathLike]],
    tile_size: int,
) -> Generator[Tuple[Path, int, int, int, int, np.ndarray], None, None]:
    for img_file in img_files:
        img = io.read_image(img_file, ignore_dtype=True)
        for x in range(0, img.shape[2], tile_size):
            for y in range(0, img.shape[1], tile_size):
                tile = img[:, y : (y + tile_size), x : (x + tile_size)]
                yield Path(img_file), x, y, tile.shape[2], tile.shape[1], tile


def combine_tiles(
    img_tile_info: Dict[str, Sequence[TileInfo]],
) -> Generator[Tuple[str, np.ndarray], None, None]:
    for img_file_stem, tile_info in img_tile_info.items():
        tile = io.read_image(tile_info[0][0], ignore_dtype=True)
        img_width = max(x + w for _, x, y, w, h in tile_info)
        img_height = max(y + h for _, x, y, w, h in tile_info)
        img = np.zeros(
            (tile.shape[0], img_height, img_width),
            dtype=tile.dtype,
        )
        for i, (tile_file, x, y, w, h) in enumerate(tile_info):
            if i > 0:
                tile = io.read_image(tile_file, ignore_dtype=True)
            img[:, y : (y + h), x : (x + w)] = tile
        yield img_file_stem, tile
