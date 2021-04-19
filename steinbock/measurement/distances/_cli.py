import click

from pathlib import Path

from steinbock.measurement.distances import distances
from steinbock.utils import cli, io


@click.group(
    name="distances",
    help="Measure spatial distances between objects",
    cls=cli.OrderedClickGroup,
)
def distances_cmd():
    pass


@distances_cmd.command(
    help="Measure distances between object centroids",
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
    "distances_dir",
    type=click.Path(file_okay=False),
    default=cli.default_distances_dir,
    show_default=True,
    help="Path to the object distances output directory",
)
def centroid(mask_dir, metric, distances_dir):
    mask_files = io.list_masks(mask_dir)
    distances_dir = Path(distances_dir)
    distances_dir.mkdir(exist_ok=True)
    it = distances.measure_centroid_distances(mask_files, metric)
    for mask_file, d in it:
        distances_file = io.write_distances(d, distances_dir / mask_file.stem)
        click.echo(distances_file)
        del d


@distances_cmd.command(
    help="Measure Euclidean distances between object borders",
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
    "distances_dir",
    type=click.Path(file_okay=False),
    default=cli.default_distances_dir,
    show_default=True,
    help="Path to the object distances output directory",
)
def border(mask_dir, distances_dir):
    mask_files = io.list_masks(mask_dir)
    distances_dir = Path(distances_dir)
    distances_dir.mkdir(exist_ok=True)
    it = distances.measure_euclidean_border_distances(mask_files)
    for mask_file, d in it:
        distances_file = io.write_distances(d, distances_dir / mask_file.stem)
        click.echo(distances_file)
        del d
