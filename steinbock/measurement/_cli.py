import click
import numpy as np

from pathlib import Path

from steinbock import cli, io
from steinbock.measurement.cellprofiler._cli import cellprofiler_cmd
from steinbock.measurement.dists._cli import dists_cmd
from steinbock.measurement.graphs import construct_graphs
from steinbock.measurement.intensities import measure_intensities
from steinbock.measurement.regionprops import measure_regionprops

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
def intensities(
    img_dir,
    mask_dir,
    panel_file,
    aggr_function_name,
    intensities_dir,
):
    aggr_function = getattr(np, aggr_function_name)
    img_files = io.list_images(img_dir)
    panel = io.read_panel(panel_file)
    channel_names = panel[io.channel_name_col].tolist()
    intensities_dir = Path(intensities_dir)
    intensities_dir.mkdir(exist_ok=True)
    for img_file, mask_file, df in measure_intensities(
        img_files,
        io.list_masks(mask_dir),
        channel_names,
        aggr_function,
    ):
        intensities_file = intensities_dir / img_file.stem
        intensities_file = io.write_data(df, intensities_file, copy=False)
        click.echo(intensities_file)
        del df


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
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default=cli.default_panel_file,
    show_default=True,
    help="Path to the panel file",
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
def regionprops(
    img_dir,
    mask_dir,
    panel_file,
    skimage_regionprops,
    regionprops_dir,
):
    img_files = io.list_images(img_dir)
    panel = io.read_panel(panel_file)
    channel_names = panel[io.channel_name_col].tolist()
    regionprops_dir = Path(regionprops_dir)
    regionprops_dir.mkdir(exist_ok=True)
    if not skimage_regionprops:
        skimage_regionprops = default_skimage_regionprops
    for img_file, mask_file, df in measure_regionprops(
        img_files,
        io.list_masks(mask_dir),
        channel_names,
        skimage_regionprops,
    ):
        regionprops_file = regionprops_dir / img_file.stem
        regionprops_file = io.write_data(df, regionprops_file, copy=False)
        click.echo(regionprops_file)
        del df


measure.add_command(dists_cmd)


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
def graphs(dists_dir, dmax, kmax, graph_dir):
    graph_dir = Path(graph_dir)
    graph_dir.mkdir(exist_ok=True)
    dists_files = io.list_distances(dists_dir)
    for dists_file, g in construct_graphs(dists_files, dmax=dmax, kmax=kmax):
        graph_file = io.write_graph(g, graph_dir / Path(dists_file).stem)
        click.echo(graph_file)
        del g


measure.add_command(cellprofiler_cmd)
