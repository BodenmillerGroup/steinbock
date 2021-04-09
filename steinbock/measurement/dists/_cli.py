import click

from pathlib import Path

from steinbock.measurement.dists.dists import (
    measure_cell_centroid_dists,
    measure_euclidean_cell_border_dists,
)
from steinbock.utils import cli, io


@click.group(
    help="Measure spatial cell-cell distances",
    cls=cli.OrderedClickGroup,
)
def dists():
    pass


@dists.command(
    name="centroid",
    help="Measure distances between cell centroids",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image .tiff directory",
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask .tiff directory",
)
@click.option(
    "--metric",
    "metric",
    type=click.STRING,
    default="euclidean",
    show_default=True,
    help="Metric supported by scipy.spatial.distance.pdist",
)
@click.option(
    "--dest",
    "cell_dists_dir",
    type=click.Path(file_okay=False),
    default=cli.default_cell_dists_dir,
    show_default=True,
    help="Path to the cell distances output directory",
)
def centroid_dists(img_dir, mask_dir, metric, cell_dists_dir):
    img_files = sorted(Path(img_dir).glob("*.tiff"))
    mask_files = sorted(Path(mask_dir).glob("*.tiff"))
    cell_dists_dir = Path(cell_dists_dir)
    cell_dists_dir.mkdir(exist_ok=True)
    it = measure_cell_centroid_dists(img_files, mask_files, metric)
    with click.progressbar(it, length=len(img_files)) as pbar:
        for img_file, mask_file, cell_dists in pbar:
            cell_dists_file_name = img_file.with_suffix(".csv").name
            cell_dists_file = cell_dists_dir / cell_dists_file_name
            io.write_cell_dists(cell_dists, cell_dists_file)


@dists.command(
    name="border",
    help="Measure Euclidean distances between cell borders",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image .tiff directory",
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask .tiff directory",
)
@click.option(
    "--dest",
    "cell_dists_dir",
    type=click.Path(file_okay=False),
    default=cli.default_cell_dists_dir,
    show_default=True,
    help="Path to the cell distances output directory",
)
def border_dists(img_dir, mask_dir, cell_dists_dir):
    img_files = sorted(Path(img_dir).glob("*.tiff"))
    mask_files = sorted(Path(mask_dir).glob("*.tiff"))
    cell_dists_dir = Path(cell_dists_dir)
    cell_dists_dir.mkdir(exist_ok=True)
    it = measure_euclidean_cell_border_dists(img_files, mask_files)
    with click.progressbar(it, length=len(img_files)) as pbar:
        for img_file, mask_file, cell_dists in pbar:
            cell_dists_file_name = img_file.with_suffix(".csv").name
            cell_dists_file = cell_dists_dir / cell_dists_file_name
            io.write_cell_dists(cell_dists, cell_dists_file)
