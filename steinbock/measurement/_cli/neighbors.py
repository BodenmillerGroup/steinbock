import click

from pathlib import Path

from steinbock import io
from steinbock._env import check_steinbock_version
from steinbock.measurement.neighbors import (
    NeighborhoodType,
    try_measure_neighbors_from_disk,
)

_neighborhood_types = {
    "centroids": NeighborhoodType.CENTROID_DISTANCE,
    "borders": NeighborhoodType.EUCLIDEAN_BORDER_DISTANCE,
    "expansion": NeighborhoodType.EUCLIDEAN_PIXEL_EXPANSION,
}


@click.command(name="neighbors", help="Measure object neighbors")
@click.option(
    "--masks",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask directory",
)
@click.option(
    "--type",
    "neighborhood_type_name",
    type=click.Choice(list(_neighborhood_types.keys()), case_sensitive=True),
    required=True,
    help="Neighborhood type",
)
@click.option(
    "--metric",
    "metric",
    type=click.STRING,
    default="euclidean",
    help="Spatial distance metric (see scipy's pdist)",
)
@click.option(
    "--dmax",
    "dmax",
    type=click.FLOAT,
    help="Maximum spatial distance between objects",
)
@click.option(
    "--kmax",
    "kmax",
    type=click.INT,
    help="Maximum number of neighbors per object",
)
@click.option(
    "-o",
    "neighbors_dir",
    type=click.Path(file_okay=False),
    default="neighbors",
    show_default=True,
    help="Path to the object neighbors output directory",
)
@check_steinbock_version
def neighbors_cmd(
    mask_dir, neighborhood_type_name, metric, dmax, kmax, neighbors_dir
):
    mask_files = io.list_mask_files(mask_dir)
    Path(neighbors_dir).mkdir(exist_ok=True)
    for mask_file, neighbors in try_measure_neighbors_from_disk(
        mask_files,
        _neighborhood_types[neighborhood_type_name],
        metric=metric,
        dmax=dmax,
        kmax=kmax,
    ):
        neighbors_stem = Path(neighbors_dir) / Path(mask_file).stem
        neighbors_file = io.write_neighbors(neighbors, neighbors_stem)
        click.echo(neighbors_file)
        del neighbors
