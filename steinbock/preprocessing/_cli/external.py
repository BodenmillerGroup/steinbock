import click
import pandas as pd

from pathlib import Path

from steinbock import io
from steinbock.preprocessing import external
from steinbock._cli import OrderedClickGroup
from steinbock._env import check_steinbock_version


@click.group(
    name="external",
    cls=OrderedClickGroup,
    help="Preprocess external image data",
)
def external_cmd_group():
    pass


@external_cmd_group.command(
    name="panel", help="Create a panel from external image data"
)
@click.option(
    "--img",
    "ext_img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="external",
    show_default=True,
    help="Path to the external image file directory",
)
@click.option(
    "-o",
    "panel_file",
    type=click.Path(dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel output file",
)
@check_steinbock_version
def panel_cmd(ext_img_dir, panel_file):
    ext_img_files = external.list_image_files(ext_img_dir)
    panel = external.create_panel_from_image_files(ext_img_files)
    io.write_panel(panel, panel_file)


@external_cmd_group.command(name="images", help="Extract external images")
@click.option(
    "--img",
    "ext_img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="external",
    show_default=True,
    help="Path to the external image file directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the steinbock panel file",
)
@click.option(
    "--imgout",
    "img_dir",
    type=click.Path(file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image output directory",
)
@click.option(
    "--infoout",
    "image_info_file",
    type=click.Path(dir_okay=False),
    default="images.csv",
    show_default=True,
    help="Path to the image information output file",
)
@check_steinbock_version
def images_cmd(ext_img_dir, panel_file, img_dir, image_info_file):
    channel_indices = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if "channel" in panel:
            channel_indices = panel["channel"].astype(int).sub(1).tolist()
    ext_img_files = external.list_image_files(ext_img_dir)
    image_info_data = []
    Path(img_dir).mkdir(exist_ok=True)
    for ext_img_file, ext_img in external.try_preprocess_images_from_disk(
        ext_img_files, channel_indices=channel_indices
    ):
        img_file = Path(img_dir) / Path(ext_img_file).stem
        img_file = io.write_image(ext_img, img_file)
        image_info_row = {
            "image": img_file.name,
            "width_px": ext_img.shape[2],
            "height_px": ext_img.shape[1],
            "num_channels": ext_img.shape[0],
        }
        image_info_data.append(image_info_row)
        click.echo(img_file)
        del ext_img
    image_info = pd.DataFrame(data=image_info_data)
    io.write_image_info(image_info, image_info_file)
