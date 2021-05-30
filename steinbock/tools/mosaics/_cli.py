import click
import re

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.tools.mosaics import mosaics


def _collect_img_files(img_files_or_dirs):
    img_files = []
    for img_file_or_dir in img_files_or_dirs:
        if Path(img_file_or_dir).is_file():
            img_files.append(Path(img_file_or_dir))
        else:
            img_files += io.list_img_files(img_file_or_dir)
    return img_files


@click.group(
    name="mosaics",
    cls=cli.OrderedClickGroup,
    help="Mosaic tiling/stitching",
)
def mosaics_cmd_group():
    pass


@mosaics_cmd_group.command(
    name="tile",
    help="Extract tiles from images",
)
@click.argument(
    "images",
    nargs=-1,
    type=click.Path(exists=True),
)
@click.option(
    "-s",
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
@check_version
def tile_cmd(images, tile_size, tile_dir):
    img_files = _collect_img_files(images)
    tile_dir = Path(tile_dir)
    tile_dir.mkdir(exist_ok=True)
    for img_file, x, y, w, h, tile in mosaics.extract_tiles_from_disk(
        img_files,
        tile_size,
    ):
        tile_file = tile_dir / f"{img_file.stem}_tx{x}_ty{y}_tw{w}_th{h}"
        tile_file = io.write_img(tile, tile_file, ignore_dtype=True)
        click.echo(tile_file)
        del tile


@mosaics_cmd_group.command(
    name="stitch",
    help="Combine tiles into images",
)
@click.argument(
    "tiles",
    nargs=-1,
    type=click.Path(exists=True),
)
@click.option(
    "-o",
    "img_dir",
    type=click.Path(file_okay=False),
    required=True,
    help="Path to the tile output directory",
)
@check_version
def stitch_cmd(tiles, img_dir):
    tile_info_groups = {}
    tile_files = _collect_img_files(tiles)
    pattern = re.compile(r"(.*)_tx(\d*)_ty(\d*)_tw(\d*)_th(\d*)")
    for tile_file in tile_files:
        match = pattern.match(tile_file.stem)
        if match:
            img_file_stem = match.group(1)
            x, y, w, h = [int(g) for g in match.group(2, 3, 4, 5)]
            if img_file_stem not in tile_info_groups:
                tile_info_groups[img_file_stem] = []
            tile_info_groups[img_file_stem].append((tile_file, x, y, w, h))
    img_dir = Path(img_dir)
    img_dir.mkdir(exist_ok=True)
    for img_file_stem, img in mosaics.stitch_tiles_from_disk(tile_info_groups):
        img_file = img_dir / img_file_stem
        img_file = io.write_img(img, img_file, ignore_dtype=True)
        click.echo(img_file)
        del img
