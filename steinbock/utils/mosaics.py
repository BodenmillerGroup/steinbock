import logging
import numpy as np
import re
import tifffile

from os import PathLike
from pathlib import Path
from typing import Dict, Generator, List, NamedTuple, Sequence, Tuple, Union


_logger = logging.getLogger(__name__)


def try_extract_tiles_from_disk_to_disk(
    img_files: Sequence[Union[str, PathLike]],
    tile_dir: Union[str, PathLike],
    tile_size: int,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for img_file in img_files:
        try:
            img = tifffile.memmap(img_file)
            for tile_x in range(0, img.shape[-1], tile_size):
                for tile_y in range(0, img.shape[-2], tile_size):
                    tile = img[
                        ...,
                        tile_y : (tile_y + tile_size),
                        tile_x : (tile_x + tile_size),
                    ]
                    tile_file = Path(tile_dir) / (
                        f"{Path(img_file).stem}_tx{tile_x}_ty{tile_y}"
                        f"_tw{tile.shape[-1]}_th{tile.shape[-2]}.tiff"
                    )
                    tifffile.imwrite(tile_file, tile)
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
        r"(?P<img_file_stem>.*)_tx(?P<x>\d*)_ty(?P<y>\d*)"
        r"_tw(?P<width>\d*)_th(?P<height>\d*)"
    )
    img_tile_infos: Dict[str, List[TileInfo]] = {}
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
            first_tile = tifffile.imread(tile_infos[0].tile_file)
            img = tifffile.memmap(
                img_file,
                shape=first_tile.shape[:-2]
                + (
                    max(ti.y + ti.height for ti in tile_infos),
                    max(ti.x + ti.width for ti in tile_infos),
                ),
                dtype=first_tile.dtype,
            )
            img[
                ...,
                tile_infos[0].y : tile_infos[0].y + tile_infos[0].height,
                tile_infos[0].x : tile_infos[0].x + tile_infos[0].width,
            ] = first_tile
            img.flush()
            for tile_info in tile_infos[1:]:
                img[
                    ...,
                    tile_info.y : tile_info.y + tile_info.height,
                    tile_info.x : tile_info.x + tile_info.width,
                ] = tifffile.imread(tile_info.tile_file)
                img.flush()
            yield img_file, img
            del img
        except:
            _logger.exception(f"Error stitching tiles: {img_file}")
