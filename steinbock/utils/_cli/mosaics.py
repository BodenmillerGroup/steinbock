import click

from os import PathLike
from pathlib import Path
from typing import List, Sequence, Union

from steinbock import io
from steinbock._cli.utils import OrderedClickGroup
from steinbock.utils import mosaics


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
    for img_file, tile_file_stem, tile in mosaics.try_extract_tiles_from_disk(
        img_files, tile_size
    ):
        tile_file = Path(tile_dir) / f"{tile_file_stem}.tiff"
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
def stitch_cmd(tiles, img_dir):
    tile_files = _collect_img_files(tiles)
    Path(img_dir).mkdir(exist_ok=True)
    for img_file_stem, img in mosaics.try_stitch_tiles_from_disk(tile_files):
        img_file = Path(img_dir) / f"{img_file_stem}.tiff"
        io.write_image(img, img_file, ignore_dtype=True)
        click.echo(img_file)
        del img
