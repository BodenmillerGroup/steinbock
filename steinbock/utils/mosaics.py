import logging
import numpy as np
import tifffile

from os import PathLike
from pathlib import Path
from typing import Generator, Mapping, NamedTuple, Sequence, Tuple, Union


_logger = logging.getLogger(__name__)


class TileInfo(NamedTuple):
    img_file_stem: str
    x: int
    y: int
    width: int
    height: int


def try_extract_tiles_from_disk(
    img_files: Sequence[Union[str, PathLike]], tile_size: int
) -> Generator[Tuple[Path, TileInfo, np.ndarray], None, None]:
    for img_file in img_files:
        try:
            img = tifffile.imread(img_file)
            img_reshaped = np.moveaxis(img, (-1, -2), (0, 1))
            for tile_x in range(0, img.shape[-1], tile_size):
                for tile_y in range(0, img.shape[-2], tile_size):
                    tile_reshaped = img_reshaped[
                        tile_x : (tile_x + tile_size),
                        tile_y : (tile_y + tile_size),
                    ]
                    tile = np.moveaxis(tile_reshaped, (0, 1), (-1, -2))
                    tile_info = TileInfo(
                        Path(img_file).stem,
                        tile_x,
                        tile_y,
                        tile.shape[-1],
                        tile.shape[-2],
                    )
                    yield Path(img_file), tile_info, tile
                    del tile, tile_reshaped
            del img, img_reshaped
        except:
            _logger.exception(f"Error extracting tiles: {img_file}")


def try_stitch_tiles_from_disk(
    img_file_stems: Sequence[str],
    img_tile_files: Mapping[str, Sequence[Union[str, PathLike]]],
    img_tile_infos: Mapping[str, Sequence[TileInfo]],
) -> Generator[Tuple[str, np.ndarray], None, None]:
    for img_file_stem in img_file_stems:
        tile_files = img_tile_files[img_file_stem]
        tile_infos = img_tile_infos[img_file_stem]
        try:
            first_tile = tifffile.imread(tile_files[0])
            first_tile_reshaped = np.moveaxis(first_tile, (-1, -2), (0, 1))
            img_reshaped = np.zeros(
                (
                    max(ti.x + ti.width for ti in tile_infos),
                    max(ti.y + ti.height for ti in tile_infos),
                )
                + first_tile_reshaped.shape[2:],
                dtype=first_tile_reshaped.dtype,
            )
            img_reshaped[
                tile_infos[0].x : tile_infos[0].x + tile_infos[0].width,
                tile_infos[0].y : tile_infos[0].y + tile_infos[0].height,
            ] = first_tile_reshaped
            del first_tile, first_tile_reshaped
            for tile_file, tile_info in zip(tile_files[1:], tile_infos[1:]):
                tile = tifffile.imread(tile_file)
                tile_reshaped = np.moveaxis(tile, (-1, -2), (0, 1))
                img_reshaped[
                    tile_info.x : tile_info.x + tile_info.width,
                    tile_info.y : tile_info.y + tile_info.height,
                ] = tile_reshaped
                del tile, tile_reshaped
            img = np.moveaxis(img_reshaped, (0, 1), (-1, -2))
            yield img_file_stem, img
            del img, img_reshaped
        except:
            _logger.exception(f"Error stitching tiles: {img_file_stem}")
