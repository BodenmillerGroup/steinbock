import logging
import numpy as np
import re
import tifffile

from os import PathLike
from pathlib import Path
from typing import Generator, NamedTuple, Sequence, Tuple, Union


_logger = logging.getLogger(__name__)


def try_extract_tiles_from_disk_to_disk(
    img_files: Sequence[Union[str, PathLike]],
    tile_dir: Union[str, PathLike],
    tile_size: int,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for img_file in img_files:
        try:
            img = tifffile.memmap(img_file, mode="r")
            if img.ndim == 6:
                img_width = img.shape[-2]
                img_height = img.shape[-3]
            else:
                img_width = img.shape[-1]
                img_height = img.shape[-2]
            if img_width % tile_size == 1 or img_height % tile_size == 1:
                _logger.warning(
                    "Chosen tile size yields UNSTITCHABLE tiles of 1 pixel "
                    f"width or height for image {img_file}"
                )
            for tile_x in range(0, img_width, tile_size):
                for tile_y in range(0, img_height, tile_size):
                    if img.ndim == 6:
                        tile = img[
                            :,
                            :,
                            :,
                            tile_y : (tile_y + tile_size),
                            tile_x : (tile_x + tile_size),
                            :,
                        ]
                        tile_width = tile.shape[-2]
                        tile_height = tile.shape[-3]
                    else:
                        tile = img[
                            ...,
                            tile_y : (tile_y + tile_size),
                            tile_x : (tile_x + tile_size),
                        ]
                        tile_width = tile.shape[-1]
                        tile_height = tile.shape[-2]
                    while tile.ndim < 5:
                        tile = np.expand_dims(tile, 0)
                    while tile.ndim < 6:
                        tile = np.expand_dims(tile, -1)
                    tile_file = Path(tile_dir) / (
                        f"{Path(img_file).stem}_tx{tile_x}_ty{tile_y}"
                        f"_tw{tile_width}_th{tile_height}.tiff"
                    )
                    tifffile.imwrite(tile_file, tile, imagej=True)
                    yield tile_file, tile
                    del tile
            del img
        except:
            _logger.exception(f"Error extracting tiles: {img_file}")


def try_stitch_tiles_from_disk_to_disk(
    tile_files: Sequence[Union[str, PathLike]],
    img_dir: Union[str, PathLike],
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
            raise ValueError(f"Malformed tile file name: {tile_file}")
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
            tile = tifffile.imread(tile_infos[0].tile_file, squeeze=False)
            img_shape = list(tile.shape)
            if tile.ndim == 6:
                img_shape[-2] = max(ti.x + ti.width for ti in tile_infos)
                img_shape[-3] = max(ti.y + ti.height for ti in tile_infos)
            else:
                img_shape[-1] = max(ti.x + ti.width for ti in tile_infos)
                img_shape[-2] = max(ti.y + ti.height for ti in tile_infos)
            img = tifffile.memmap(
                img_file,
                shape=tuple(img_shape),
                dtype=tile.dtype,
                imagej=True,
            )
            for i, tile_info in enumerate(tile_infos):
                if i > 0:
                    tile = tifffile.imread(tile_info.tile_file, squeeze=False)
                if tile.ndim == 6:
                    img[
                        :,
                        :,
                        :,
                        tile_info.y : tile_info.y + tile_info.height,
                        tile_info.x : tile_info.x + tile_info.width,
                        :,
                    ] = tile
                else:
                    img[
                        :,
                        :,
                        :,
                        tile_info.y : tile_info.y + tile_info.height,
                        tile_info.x : tile_info.x + tile_info.width,
                    ] = tile
                img.flush()
            yield img_file, img
            del img
        except:
            _logger.exception(f"Error stitching tiles: {img_file}")
