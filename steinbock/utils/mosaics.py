import logging
import numpy as np
import re

from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)


def try_extract_tiles_from_disk(
    img_files: Sequence[Union[str, PathLike]], tile_size: int
) -> Generator[Tuple[Path, str, np.ndarray], None, None]:
    for img_file in img_files:
        try:
            img = io.read_image(img_file, native_dtype=True)
            for tile_x in range(0, img.shape[-1], tile_size):
                for tile_y in range(0, img.shape[-2], tile_size):
                    tile = img[
                        :,
                        tile_y : (tile_y + tile_size),
                        tile_x : (tile_x + tile_size),
                    ]
                    tile_file_stem = (
                        f"{Path(img_file).stem}"
                        f"_x{tile_x}_y{tile_y}"
                        f"_w{tile.shape[-1]}_h{tile.shape[-2]}"
                    )
                    yield Path(img_file), tile_file_stem, tile
                    del tile
            del img
        except:
            _logger.exception(f"Error extracting tiles: {img_file}")


def try_stitch_tiles_from_disk(
    tile_files: Sequence[Union[str, PathLike]]
) -> Generator[Tuple[str, np.ndarray], None, None]:
    img_tile_infos = {}
    tile_file_stem_pattern = re.compile(r"(.*)_x(\d*)_y(\d*)_w(\d*)_h(\d*)")
    for tile_file in tile_files:
        m = tile_file_stem_pattern.fullmatch(Path(tile_file).stem)
        if m is None:
            _logger.warning(f"Malformed file name, ignoring file {tile_file}")
            continue
        img_file_stem, tile_x, tile_y, tile_w, tile_h = m.group(1, 2, 3, 4, 5)
        if img_file_stem not in img_tile_infos:
            img_tile_infos[img_file_stem] = []
        img_tile_infos[img_file_stem].append(
            (tile_file, tile_x, tile_y, tile_w, tile_h)
        )
    for img_file_stem, tile_infos in img_tile_infos:
        try:
            tile_file, tile_x, tile_y, tile_w, tile_h = tile_infos[0]
            tile = io.read_image(tile_file, native_dtype=True)
            img = np.zeros(
                (
                    tile.shape[0],
                    max(x + w for _, x, y, w, h in tile_infos),
                    max(y + h for _, x, y, w, h in tile_infos),
                ),
                dtype=tile.dtype,
            )
            img[:, tile_y : tile_y + tile_h, tile_x : tile_x + tile_w] = tile
            for tile_file, tile_x, tile_y, tile_w, tile_h in tile_infos[1:]:
                img[
                    :, tile_y : tile_y + tile_h, tile_x : tile_x + tile_w
                ] = io.read_image(tile_file, native_dtype=True)
            yield img_file_stem, img
            del img
        except:
            _logger.exception(f"Error stitching tiles: {img_file_stem}")
