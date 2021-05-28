import click

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.measurement.dists import dists


@click.group(
    name="distances",
    help="Measure spatial distances between objects",
    cls=cli.OrderedClickGroup,
)
def distances_cmd_group():
    pass


@distances_cmd_group.command(
    name="centroids",
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
    "dists_dir",
    type=click.Path(file_okay=False),
    default=cli.default_dists_dir,
    show_default=True,
    help="Path to the object distances output directory",
)
@check_version
def centroids_cmd(mask_dir, metric, dists_dir):
    dists_dir = Path(dists_dir)
    dists_dir.mkdir(exist_ok=True)
    for mask_file, df in dists.measure_centroid_distances_from_disk(
        io.list_mask_files(mask_dir),
        metric,
    ):
        dists_file = dists_dir / mask_file.stem
        dists_file = io.write_distances(df, dists_file, copy=False)
        click.echo(dists_file)
        del df


@distances_cmd_group.command(
    name="borders",
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
    "dists_dir",
    type=click.Path(file_okay=False),
    default=cli.default_dists_dir,
    show_default=True,
    help="Path to the object distances output directory",
)
@check_version
def borders_cmd(mask_dir, dists_dir):
    dists_dir = Path(dists_dir)
    dists_dir.mkdir(exist_ok=True)
    for mask_file, df in dists.measure_euclidean_border_distances_from_disk(
        io.list_mask_files(mask_dir),
    ):
        dists_file = dists_dir / mask_file.stem
        dists_file = io.write_distances(df, dists_file, copy=False)
        click.echo(dists_file)
        del df
