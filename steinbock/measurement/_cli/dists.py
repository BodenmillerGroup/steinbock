import click

from pathlib import Path

from steinbock import io
from steinbock._cli.utils import OrderedClickGroup
from steinbock._env import check_steinbock_version
from steinbock.measurement import distances


@click.group(
    name="distances",
    help="Measure spatial distances between objects",
    cls=OrderedClickGroup,
)
def distances_cmd_group():
    pass


@distances_cmd_group.command(
    name="centroids", help="Measure distances between object centroids"
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default="masks",
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
    "dists_dir",
    type=click.Path(file_okay=False),
    default="distances",
    show_default=True,
    help="Path to the object distances output directory",
)
@check_steinbock_version
def centroids_cmd(mask_dir, metric, dists_dir):
    mask_files = io.list_mask_files(mask_dir)
    Path(dists_dir).mkdir(exist_ok=True)
    for mask_file, dists in distances.measure_centroid_distances_from_disk(
        mask_files, metric
    ):
        dists_stem = Path(dists_dir) / mask_file.stem
        dists_file = io.write_distances(dists, dists_stem, copy=False)
        click.echo(dists_file)
        del dists


@distances_cmd_group.command(
    name="borders", help="Measure Euclidean distances between object borders"
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask .tiff directory",
)
@click.option(
    "--dest",
    "dists_dir",
    type=click.Path(file_okay=False),
    default="distances",
    show_default=True,
    help="Path to the object distances output directory",
)
@check_steinbock_version
def borders_cmd(mask_dir, dists_dir):
    mask_files = io.list_mask_files(mask_dir)
    Path(dists_dir).mkdir(exist_ok=True)
    for (
        mask_file,
        dists,
    ) in distances.measure_euclidean_border_distances_from_disk(mask_files):
        dists_stem = Path(dists_dir) / mask_file.stem
        dists_file = io.write_distances(dists, dists_stem, copy=False)
        click.echo(dists_file)
        del dists
