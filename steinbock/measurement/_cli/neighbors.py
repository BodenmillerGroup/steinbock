import click

from pathlib import Path

from ..neighbors import NeighborhoodType, try_measure_neighbors_from_disk
from ... import io

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
    "--mmap/--no-mmap",
    "mmap",
    default=False,
    show_default=True,
    help="Use memory mapping for reading images/masks",
)
@click.option(
    "-o",
    "neighbors_dir",
    type=click.Path(file_okay=False),
    default="neighbors",
    show_default=True,
    help="Path to the object neighbors output directory",
)
def neighbors_cmd(
    mask_dir, neighborhood_type_name, metric, dmax, kmax, mmap, neighbors_dir
):
    mask_files = io.list_mask_files(mask_dir)
    Path(neighbors_dir).mkdir(exist_ok=True)
    for mask_file, neighbors in try_measure_neighbors_from_disk(
        mask_files,
        _neighborhood_types[neighborhood_type_name],
        metric=metric,
        dmax=dmax,
        kmax=kmax,
        mmap=mmap,
    ):
        neighbors_file = io._as_path_with_suffix(
            Path(neighbors_dir) / Path(mask_file).name, ".csv"
        )
        io.write_neighbors(neighbors, neighbors_file)
        click.echo(neighbors_file)
        del neighbors
