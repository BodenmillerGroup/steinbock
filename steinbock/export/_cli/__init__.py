import click
import numpy as np

from pathlib import Path
from tifffile import imwrite
from xtiff import to_tiff

from steinbock import io
from steinbock.export._cli.data import anndata_cmd, csv_cmd, fcs_cmd
from steinbock.export._cli.graphs import graphs_cmd
from steinbock._cli.utils import OrderedClickGroup
from steinbock._env import check_steinbock_version


@click.group(
    name="export",
    cls=OrderedClickGroup,
    help="Export data to third-party formats",
)
def export_cmd_group():
    pass


@export_cmd_group.command(name="ome", help="Export images as OME-TIFF")
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel file",
)
@click.option(
    "-o",
    "ome_dir",
    type=click.Path(file_okay=False),
    default="ome",
    show_default=True,
    help="Path to the OME-TIFF export directory",
)
@check_steinbock_version
def ome_cmd(img_dir, panel_file, ome_dir):
    panel = io.read_panel(panel_file)
    channel_names = [
        f"{channel_id}_{channel_name}"
        for channel_id, channel_name in zip(
            panel["channel"].values, panel["name"].values
        )
    ]
    Path(ome_dir).mkdir(exist_ok=True)
    for img_file in io.list_image_files(img_dir):
        img = io.read_image(img_file)
        ome_file = io._as_path_with_suffix(
            Path(ome_dir) / img_file.name, ".ome.tiff"
        )
        to_tiff(img, ome_file, channel_names=channel_names)
        click.echo(ome_file.name)
        del img


@export_cmd_group.command(
    name="histocat", help="Export images to histoCAT for MATLAB"
)
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
    type=click.Path(file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel file",
)
@click.option(
    "-o",
    "histocat_dir",
    type=click.Path(file_okay=False),
    default="histocat",
    show_default=True,
    help="Path to the histoCAT export directory",
)
@check_steinbock_version
def histocat_cmd(img_dir, mask_dir, panel_file, histocat_dir):
    panel = io.read_panel(panel_file)
    channel_names = [
        f"{channel_id}_{channel_name}"
        for channel_id, channel_name in zip(
            panel["channel"].values, panel["name"].values
        )
    ]
    img_files = io.list_image_files(img_dir)
    mask_files = None
    if Path(mask_dir).exists():
        mask_files = io.list_mask_files(mask_dir, base_files=img_files)
    Path(histocat_dir).mkdir(exist_ok=True)
    for i, img_file in enumerate(img_files):
        img = io.read_image(img_file, native_dtype=True)
        histocat_img_dir = Path(histocat_dir) / img_file.stem
        histocat_img_dir.mkdir(exist_ok=True)
        for channel_name, channel_img in zip(channel_names, img):
            imwrite(
                histocat_img_dir / f"{channel_name}.tiff",
                data=io._to_dtype(channel_img, np.float32),
                imagej=True,
            )
        mask = None
        if mask_files is not None:
            mask = io.read_mask(mask_files[i])
            imwrite(
                histocat_img_dir / f"{img_file.stem}_mask.tiff",
                data=io._to_dtype(mask, np.uint16),
                imagej=True,
            )
        click.echo(img_file.name)
        del img, mask


export_cmd_group.add_command(csv_cmd)
export_cmd_group.add_command(fcs_cmd)
export_cmd_group.add_command(anndata_cmd)
export_cmd_group.add_command(graphs_cmd)
