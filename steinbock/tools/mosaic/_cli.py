import click
import re

from pathlib import Path

from steinbock.tools.mosaic import mosaic
from steinbock.utils import cli, io


@click.group(
    name="mosaic",
    cls=cli.OrderedClickGroup,
    help="Tile/stitch .tiff images",
)
def mosaic_cmd():
    pass


@mosaic_cmd.command(
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
def tile(images, tile_size, tile_dir):
    img_files = []
    for image in images:
        if Path(image).is_dir():
            img_files += io.list_images(image)
        else:
            img_files.append(Path(image))
    tile_dir = Path(tile_dir)
    tile_dir.mkdir(exist_ok=True)
    it = mosaic.extract_tiles(img_files, tile_size)
    for img_file, x, y, w, h, tile in it:
        tile_file = tile_dir / f"{img_file.stem}_tx{x}_ty{y}_tw{w}_th{h}"
        tile_file = io.write_image(tile, tile_file, ignore_dtype=True)
        click.echo(tile_file)


@mosaic_cmd.command(
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
def stitch(tiles, img_dir):
    tile_files = []
    for tile in tiles:
        if Path(tile).is_dir():
            tile_files += io.list_images(tile)
        else:
            tile_files.append(Path(tile))
    img_tile_info = {}
    pattern = re.compile(r"(.*)_tx(\d*)_ty(\d*)_tw(\d*)_th(\d*)")
    for tile_file in tile_files:
        match = pattern.match(tile_file.stem)
        if match:
            img_file_stem = match.group(1)
            x, y, w, h = [int(g) for g in pattern.group(2, 3, 4, 5)]
            if img_file_stem not in img_tile_info:
                img_tile_info[img_file_stem] = []
            img_tile_info[img_file_stem].append((tile_file, x, y, w, h))
    img_dir = Path(img_dir)
    img_dir.mkdir(exist_ok=True)
    it = mosaic.combine_tiles(img_tile_info)
    with click.progressbar(it, length=len(img_tile_info)) as pbar:
        for img_file_stem, img in pbar:
            img_file = img_dir / img_file_stem
            img_file = io.write_image(img, img_file, ignore_dtype=True)
