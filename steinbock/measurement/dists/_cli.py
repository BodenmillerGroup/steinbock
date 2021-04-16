import click

from pathlib import Path

from steinbock.measurement.dists import dists
from steinbock.utils import cli, io


@click.group(
    name="dists",
    help="Measure spatial cell-cell distances",
    cls=cli.OrderedClickGroup,
)
def dists_cmd():
    pass


@dists_cmd.command(
    help="Measure distances between cell centroids",
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask directory",
)
@click.option(
    "--metric",
    "metric",
    type=click.STRING,
    default="euclidean",
    show_default=True,
    help=(
        "Spatial distance metric, see "
        "https://docs.scipy.org/doc/scipy/reference/generated/"
        "scipy.spatial.distance.pdist.html"
    ),
)
@click.option(
    "--dest",
    "cell_dists_dir",
    type=click.Path(file_okay=False),
    default=cli.default_cell_dists_dir,
    show_default=True,
    help="Path to the cell distances output directory",
)
def centroid(mask_dir, metric, cell_dists_dir):
    mask_files = io.list_masks(mask_dir)
    cell_dists_dir = Path(cell_dists_dir)
    cell_dists_dir.mkdir(exist_ok=True)
    for mask_file, cell_dists in dists.measure_cell_centroid_dists(
        mask_files,
        metric,
    ):
        cell_dists_file = cell_dists_dir / mask_file.stem
        cell_dists_file = io.write_cell_dists(cell_dists, cell_dists_file)
        click.echo(cell_dists_file)
        del cell_dists


@dists_cmd.command(
    help="Measure Euclidean distances between cell borders",
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
def border(mask_dir, cell_dists_dir):
    mask_files = io.list_masks(mask_dir)
    cell_dists_dir = Path(cell_dists_dir)
    cell_dists_dir.mkdir(exist_ok=True)
    for mask_file, cell_dists in dists.measure_euclidean_cell_border_dists(
        mask_files,
    ):
        cell_dists_file = cell_dists_dir / mask_file.stem
        cell_dists_file = io.write_cell_dists(cell_dists, cell_dists_file)
        click.echo(cell_dists_file)
        del cell_dists
