from pathlib import Path

import click
import click_log
import pandas as pd

from ... import io
from ..._cli.utils import (
    OrderedClickGroup,
    SteinbockCLIException,
    catch_exception,
    logger,
)
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import imc

imc_cli_available = imc.imc_available


@click.group(
    name="imc",
    cls=OrderedClickGroup,
    help="Preprocess Imaging Mass Cytometry (IMC) data",
)
def imc_cmd_group():
    pass


@imc_cmd_group.command(name="panel", help="Create a panel from IMC panel/image data")
@click.option(
    "--imcpanel",
    "imc_panel_file",
    type=click.Path(dir_okay=False),
    default=str(Path("raw", "panel.csv")),
    show_default=True,
    help="Path to the IMC panel file",
)
@click.option(
    "--channelcol",
    "imc_panel_channel_col",
    type=click.STRING,
    default="Metal Tag",
    show_default=True,
    help="IMC panel column containing the channel (required)",
)
@click.option(
    "--namecol",
    "imc_panel_name_col",
    type=click.STRING,
    default="Target",
    show_default=True,
    help="IMC panel column containing the channel name (required)",
)
@click.option(
    "--keepcol",
    "imc_panel_keep_col",
    type=click.STRING,
    default="full",
    show_default=True,
    help="IMC panel column indicating whether to keep the channel (0/1)",
)
@click.option(
    "--ilastikcol",
    "imc_panel_ilastik_col",
    type=click.STRING,
    default="ilastik",
    show_default=True,
    help="IMC panel column indicating Ilastik usage (0/1)",
)
@click.option(
    "--mcd",
    "mcd_dir",
    type=click.Path(file_okay=False),
    default="raw",
    show_default=True,
    help="Path to the IMC .mcd/.zip file directory",
)
@click.option(
    "--txt",
    "txt_dir",
    type=click.Path(file_okay=False),
    default="raw",
    show_default=True,
    help="Path to the IMC .txt/.zip file directory",
)
@click.option(
    "--unzip/--no-unzip",
    "unzip",
    default=True,
    show_default=True,
    help="Unzip .mcd/.txt files from .zip archives",
)
@click.option(
    "-o",
    "panel_file",
    type=click.Path(dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel output file",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def panel_cmd(
    imc_panel_file,
    imc_panel_channel_col,
    imc_panel_name_col,
    imc_panel_keep_col,
    imc_panel_ilastik_col,
    mcd_dir,
    txt_dir,
    unzip,
    panel_file,
):
    panel = None
    if panel is None and Path(imc_panel_file).is_file():
        panel = imc.create_panel_from_imc_panel(
            imc_panel_file,
            imc_panel_channel_col=imc_panel_channel_col,
            imc_panel_name_col=imc_panel_name_col,
            imc_panel_keep_col=imc_panel_keep_col,
            imc_panel_ilastik_col=imc_panel_ilastik_col,
        )
    if panel is None and Path(mcd_dir).is_dir():
        mcd_files = imc.list_mcd_files(mcd_dir, unzip=unzip)
        if len(mcd_files) > 0:
            panel = imc.create_panel_from_mcd_files(mcd_files, unzip=unzip)
    if panel is None and Path(txt_dir).is_dir():
        txt_files = imc.list_txt_files(txt_dir, unzip=unzip)
        if len(txt_files) > 0:
            panel = imc.create_panel_from_txt_files(txt_files, unzip=unzip)
    if panel is None:
        raise SteinbockCLIException("No panel/.mcd/.txt file found")
    io.write_panel(panel, panel_file)
    logger.info(panel_file)


@imc_cmd_group.command(
    name="images", help="Extract Imaging Mass Cytometry (IMC) images"
)
@click.option(
    "--mcd",
    "mcd_dir",
    type=click.Path(exists=True, file_okay=False),
    default="raw",
    show_default=True,
    help="Path to the IMC .mcd/.zip file directory",
)
@click.option(
    "--txt",
    "txt_dir",
    type=click.Path(exists=True, file_okay=False),
    default="raw",
    show_default=True,
    help="Path to the IMC .txt/.zip file directory",
)
@click.option(
    "--unzip/--no-unzip",
    "unzip",
    default=True,
    show_default=True,
    help="Unzip .mcd/.txt files from .zip archives",
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
    "--hpf",
    "hpf",
    type=click.FLOAT,
    help="Hot pixel filter (specify delta threshold)",
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
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def images_cmd(mcd_dir, txt_dir, unzip, panel_file, hpf, img_dir, image_info_file):
    channel_names = None
    if Path(panel_file).is_file():
        panel = io.read_panel(panel_file)
        if "channel" in panel:
            channel_names = panel["channel"].tolist()
    image_info_data = []
    Path(img_dir).mkdir(exist_ok=True)
    mcd_files = imc.list_mcd_files(mcd_dir, unzip=unzip)
    txt_files = imc.list_txt_files(txt_dir, unzip=unzip)
    mcd_txt_files = {}
    num_dupl = 0
    for (
        mcd_or_txt_file,
        acquisition,
        img,
        recovery_txt_file,
        recovered,
    ) in imc.try_preprocess_images_from_disk(
        mcd_files, txt_files, channel_names=channel_names, hpf=hpf, unzip=unzip
    ):
        img_file_stem = Path(mcd_or_txt_file).stem
        if acquisition is not None:
            img_file_stem += f"_{acquisition.id:03d}"
        if img_file_stem in mcd_txt_files:
            num_dupl += 1
            first_mcd_txt_file = mcd_txt_files[img_file_stem][0]
            img_file_stem = f"DUPLICATE{num_dupl:03d}_{img_file_stem}"
            logger.warning(
                f"File {mcd_or_txt_file} is a duplicate of {first_mcd_txt_file}, "
                f"saving as {img_file_stem}"
            )
            mcd_txt_files[img_file_stem].append(mcd_or_txt_file)
        else:
            mcd_txt_files[img_file_stem] = [mcd_or_txt_file]
        img_file = Path(img_dir) / f"{img_file_stem}.tiff"
        io.write_image(img, img_file)
        image_info_row = imc.create_image_info(
            mcd_or_txt_file, acquisition, img, recovery_txt_file, recovered, img_file
        )
        image_info_data.append(image_info_row)
        logger.info(img_file)
        del img
    image_info = pd.DataFrame(data=image_info_data)
    io.write_image_info(image_info, image_info_file)
    logger.info(image_info_file)
