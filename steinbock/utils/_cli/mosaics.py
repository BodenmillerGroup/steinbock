import click
import re

from pathlib import Path

from steinbock import io
from steinbock._cli.utils import OrderedClickGroup
from steinbock._env import check_steinbock_version
from steinbock.utils import mosaics


def _collect_img_files(img_files_or_dirs):
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
@check_steinbock_version
def tile_cmd(images, tile_size, tile_dir):
    img_files = _collect_img_files(images)
    Path(tile_dir).mkdir(exist_ok=True)
    for img_file, x, y, tile in mosaics.try_extract_tiles_from_disk(
        img_files, tile_size
    ):
        tile_stem = (
            Path(tile_dir)
            / f"{img_file.stem}_tx{x}_ty{y}_tw{tile_size}_th{tile_size}"
        )
        tile_file = io.write_image(tile, tile_stem, ignore_dtype=True)
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
@check_steinbock_version
def stitch_cmd(tiles, img_dir):
    tile_info_groups = {}
    tile_files = _collect_img_files(tiles)
    pattern = re.compile(r"(.*)_tx(\d*)_ty(\d*)_tw(\d*)_th(\d*)")
    for tile_file in tile_files:
        match = pattern.match(tile_file.stem)
        if match:
            img_stem_name = match.group(1)
            x, y, w, h = [int(g) for g in match.group(2, 3, 4, 5)]
            if img_stem_name not in tile_info_groups:
                tile_info_groups[img_stem_name] = []
            tile_info_groups[img_stem_name].append((tile_file, x, y, w, h))
    Path(img_dir).mkdir(exist_ok=True)
    for img_stem_name, img in mosaics.try_stitch_tiles_from_disk(
        tile_info_groups
    ):
        img_stem = Path(img_dir) / img_stem_name
        img_file = io.write_image(img, img_stem, ignore_dtype=True)
        click.echo(img_file)
        del img
