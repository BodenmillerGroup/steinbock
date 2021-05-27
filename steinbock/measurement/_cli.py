import click
import numpy as np

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.measurement.cellprofiler._cli import cellprofiler_cmd
from steinbock.measurement.dists._cli import distances_cmd
from steinbock.measurement.graphs import construct_graphs_from_disk
from steinbock.measurement.intensities import measure_intensities_from_disk
from steinbock.measurement.regionprops import measure_regionprops_from_disk

default_skimage_regionprops = [
    "area",
    "centroid",
    "major_axis_length",
    "minor_axis_length",
    "eccentricity",
]


@click.group(
    cls=cli.OrderedClickGroup,
    help="Extract object data from segmented images",
)
def measure():
    pass


@measure.command(
    help="Measure object intensities",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image directory",
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
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default=cli.default_panel_file,
    show_default=True,
    help="Path to the panel file",
)
@click.option(
    "--aggr",
    "aggr_function_name",
    type=click.STRING,
    default="mean",
    show_default=True,
    help="Numpy function for aggregating pixels",
)
@click.option(
    "--dest",
    "intensities_dir",
    type=click.Path(file_okay=False),
    default=cli.default_intensities_dir,
    show_default=True,
    help="Path to the object intensities output directory",
)
@check_version
def intensities(
    img_dir,
    mask_dir,
    panel_file,
    aggr_function_name,
    intensities_dir,
):
    panel = io.read_panel(panel_file)
    channel_names = panel[io.channel_name_col].tolist()
    aggr_function = getattr(np, aggr_function_name)
    intensities_dir = Path(intensities_dir)
    intensities_dir.mkdir(exist_ok=True)
    for img_file, mask_file, intensities in measure_intensities_from_disk(
        io.list_image_files(img_dir),
        io.list_mask_files(mask_dir),
        channel_names,
        aggr_function,
    ):
        intensities_file = io.write_data(
            intensities,
            intensities_dir / img_file.stem,
            copy=False,
        )
        click.echo(intensities_file)
        del intensities


@measure.command(
    help="Measure object region properties",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask directory",
)
@click.argument(
    "skimage_regionprops",
    nargs=-1,
    type=click.STRING,
)
@click.option(
    "--dest",
    "regionprops_dir",
    type=click.Path(file_okay=False),
    default=cli.default_regionprops_dir,
    show_default=True,
    help="Path to the object region properties output directory",
)
@check_version
def regionprops(
    img_dir,
    mask_dir,
    skimage_regionprops,
    regionprops_dir,
):
    regionprops_dir = Path(regionprops_dir)
    regionprops_dir.mkdir(exist_ok=True)
    if not skimage_regionprops:
        skimage_regionprops = default_skimage_regionprops
    for img_file, mask_file, regionprops in measure_regionprops_from_disk(
        io.list_image_files(img_dir),
        io.list_mask_files(mask_dir),
        skimage_regionprops,
    ):
        regionprops_file = io.write_data(
            regionprops,
            regionprops_dir / img_file.stem,
            copy=False
        )
        click.echo(regionprops_file)
        del regionprops


measure.add_command(distances_cmd)


@measure.command(
    help="Construct spatial object neighborhood graphs",
)
@click.option(
    "--dists",
    "dists_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_dists_dir,
    show_default=True,
    help="Path to the object distances directory",
)
@click.option(
    "--dmax",
    "dmax",
    type=click.FLOAT,
    help="Maximum distance between objects",
)
@click.option(
    "--kmax",
    "kmax",
    type=click.INT,
    help="Maximum number of neighbors per object",
)
@click.option(
    "--dest",
    "graph_dir",
    type=click.Path(file_okay=False),
    default=cli.default_graph_dir,
    show_default=True,
    help="Path to the object graph output directory",
)
@check_version
def graphs(dists_dir, dmax, kmax, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    for dists_file, graph in construct_graphs_from_disk(
        io.list_distances_files(dists_dir),
        dmax=dmax,
        kmax=kmax,
    ):
        graph_file = io.write_graph(graph, graph_dir / Path(dists_file).stem)
        click.echo(graph_file)
        del graph


measure.add_command(cellprofiler_cmd)
