import click
import re
import sys

from os import PathLike
from pathlib import Path
from skimage import measure
from typing import List, Sequence, Union

from steinbock import io
from steinbock._cli.utils import OrderedClickGroup
from steinbock.utils import mosaics
from steinbock.utils.mosaics import TileInfo


def _collect_img_files(
    img_files_or_dirs: Sequence[Union[str, PathLike]]
) -> List[Path]:
    img_files = []
    for img_file_or_dir in img_files_or_dirs:
        if Path(img_file_or_dir).is_file():
            img_files.append(Path(img_file_or_dir))
        else:
            img_files += io.list_image_files(img_file_or_dir)
    return img_files


@click.group(
    name="mosaics", cls=OrderedClickGroup, help="Mosaic tiling/stitching"
)
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
    "-o",
    "tile_dir",
    type=click.Path(file_okay=False),
    required=True,
    help="Path to the tile output directory",
)
def tile_cmd(images, tile_size, tile_dir):
    img_files = _collect_img_files(images)
    Path(tile_dir).mkdir(exist_ok=True)
    for img_file, tile_info, tile in mosaics.try_extract_tiles_from_disk(
        img_files, tile_size
    ):
        tile_file = Path(tile_dir) / (
            f"{tile_info.img_file_stem}_tx{tile_info.x}_ty{tile_info.y}"
            f"_tw{tile_info.width}_th{tile_info.height}.tiff"
        )
        io.write_image(tile, tile_file, ignore_dtype=True)
        click.echo(tile_file)
        del tile


@mosaics_cmd_group.command(name="stitch", help="Combine tiles into images")
@click.argument("tiles", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-o",
    "img_dir",
    type=click.Path(file_okay=False),
    required=True,
    help="Path to the tile output directory",
)
@click.option(
    "--relabel/--no-relabel",
    "relabel",
    default=False,
    show_default=True,
    help="Relabel objects",
)
def stitch_cmd(tiles, img_dir, relabel):
    tile_files = _collect_img_files(tiles)
    Path(img_dir).mkdir(exist_ok=True)
    tile_file_stem_pattern = re.compile(
        r"(?P<img_file_stem>.*)_tx(?P<x>\d*)_ty(?P<y>\d*)"
        r"_tw(?P<width>\d*)_th(?P<height>\d*)"
    )
    img_file_stems = []
    img_tile_files = {}
    img_tile_infos = {}
    for tile_file in tile_files:
        m = tile_file_stem_pattern.fullmatch(tile_file.stem)
        if m is None:
            click.echo(
                f"WARNING: Malformed file name, ignoring file {tile_file}",
                file=sys.stderr,
            )
            continue
        tile_info = TileInfo(
            m.group("img_file_stem"),
            int(m.group("x")),
            int(m.group("y")),
            int(m.group("width")),
            int(m.group("height")),
        )
        if tile_info.img_file_stem not in img_file_stems:
            img_file_stems.append(tile_info.img_file_stem)
            img_tile_files[tile_info.img_file_stem] = []
            img_tile_infos[tile_info.img_file_stem] = []
        img_tile_files[tile_info.img_file_stem].append(tile_file)
        img_tile_infos[tile_info.img_file_stem].append(tile_info)
    for img_file_stem, img in mosaics.try_stitch_tiles_from_disk(
        img_file_stems, img_tile_files, img_tile_infos
    ):
        if relabel:
            if img.ndim != 2:
                click.echo(
                    f"WARNING: Failed to relabel image with shape {img.shape}",
                    file=sys.stderr,
                )
                continue
            img = measure.label(img)
        img_file = Path(img_dir) / f"{img_file_stem}.tiff"
        io.write_image(img, img_file, ignore_dtype=True)
        click.echo(img_file)
        del img
