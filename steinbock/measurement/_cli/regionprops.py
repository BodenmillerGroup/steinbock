import click

from pathlib import Path

from steinbock import io
from steinbock._env import check_steinbock_version
from steinbock.measurement.regionprops import try_measure_regionprops_from_disk


@click.command(name="regionprops", help="Measure object region properties")
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--mask",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask directory",
)
@click.argument("skimage_regionprops", nargs=-1, type=click.STRING)
@click.option(
    "-o",
    "regionprops_dir",
    type=click.Path(file_okay=False),
    default="regionprops",
    show_default=True,
    help="Path to the object region properties output directory",
)
@check_steinbock_version
def regionprops_cmd(img_dir, mask_dir, skimage_regionprops, regionprops_dir):
    img_files = io.list_image_files(img_dir)
    mask_files = io.list_mask_files(mask_dir, base_files=img_files)
    Path(regionprops_dir).mkdir(exist_ok=True)
    if not skimage_regionprops:
        skimage_regionprops = [
            "area",
            "centroid",
            "major_axis_length",
            "minor_axis_length",
            "eccentricity",
        ]
    for img_file, mask_file, regionprops in try_measure_regionprops_from_disk(
        img_files, mask_files, skimage_regionprops
    ):
        regionprops_stem = Path(regionprops_dir) / img_file.stem
        regionprops_file = io.write_data(regionprops, regionprops_stem)
        click.echo(regionprops_file)
        del regionprops
