import click

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.measurement.regionprops import regionprops


default_skimage_regionprops = [
    "area",
    "centroid",
    "major_axis_length",
    "minor_axis_length",
    "eccentricity",
]


@click.command(
    name="regionprops",
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
def regionprops_cmd(
    img_dir,
    mask_dir,
    skimage_regionprops,
    regionprops_dir,
):
    regionprops_dir = Path(regionprops_dir)
    regionprops_dir.mkdir(exist_ok=True)
    if not skimage_regionprops:
        skimage_regionprops = default_skimage_regionprops
    for img_file, mask_file, df in regionprops.measure_regionprops_from_disk(
        io.list_img_files(img_dir),
        io.list_mask_files(mask_dir),
        skimage_regionprops,
    ):
        regionprops_file = regionprops_dir / img_file.stem
        regionprops_file = io.write_data(df, regionprops_file, copy=False)
        click.echo(regionprops_file)
        del df
