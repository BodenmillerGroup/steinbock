import shutil
import sys
from pathlib import Path

import click
import click_log
import numpy as np

from ... import io
from ..._cli.utils import (
    OrderedClickGroup,
    SteinbockCLIException,
    catch_exception,
    logger,
)
from ..._env import use_ilastik_env
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import ilastik


@click.group(
    name="ilastik",
    cls=OrderedClickGroup,
    help="Perform supervised pixel classification using Ilastik",
)
def ilastik_cmd_group():
    pass


@ilastik_cmd_group.command(
    name="prepare", help="Prepare an Ilastik project file, images and crops"
)
@click.option(
    "-o",
    "ilastik_project_file",
    type=click.Path(dir_okay=False),
    default="pixel_classifier.ilp",
    show_default=True,
    help="Path to the Ilastik project output file",
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
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel file",
)
@click.option(
    "--aggr",
    "aggr_func_name",
    type=click.STRING,
    default="mean",
    show_default=True,
    help="Numpy function for aggregating channel pixels",
)
@click.option(
    "--mean/--no-mean",
    "prepend_mean",
    default=True,
    show_default=True,
    help="Prepend mean of all channels as a new channel",
)
@click.option(
    "--meanfactor",
    "mean_factor",
    type=click.FLOAT,
    default=100.0,
    show_default=True,
    help="Factor to multiply the channels mean with",
)
@click.option(
    "--scale",
    "scale_factor",
    type=click.INT,
    default=2,
    show_default=True,
    help="Ilastik image scale factor",
)
@click.option(
    "--cropsize",
    "ilastik_crop_size",
    type=click.INT,
    default=512,
    show_default=True,
    help="Ilastik crop size (in pixels)",
)
@click.option(
    "--imgout",
    "ilastik_img_dir",
    type=click.Path(file_okay=False),
    default="ilastik_img",
    show_default=True,
    help="Path to the Ilastik image output directory",
)
@click.option(
    "--cropout",
    "ilastik_crop_dir",
    type=click.Path(file_okay=False),
    default="ilastik_crops",
    show_default=True,
    help="Path to the Ilastik crop output directory",
)
@click.option("--seed", "seed", type=click.INT, help="Random seed")
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def prepare_cmd(
    ilastik_project_file,
    img_dir,
    panel_file,
    aggr_func_name,
    prepend_mean,
    mean_factor,
    scale_factor,
    ilastik_crop_size,
    ilastik_img_dir,
    ilastik_crop_dir,
    seed,
):
    channel_groups = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if "ilastik" in panel and panel["ilastik"].notna().any():
            channel_groups = panel["ilastik"].values
    aggr_func = getattr(np, aggr_func_name)
    img_files = io.list_image_files(img_dir)
    Path(ilastik_img_dir).mkdir(exist_ok=True)
    ilastik_img_files = []
    for img_file, ilastik_img in ilastik.try_create_ilastik_images_from_disk(
        img_files,
        channel_groups=channel_groups,
        aggr_func=aggr_func,
        prepend_mean=prepend_mean,
        mean_factor=mean_factor,
        scale_factor=scale_factor,
    ):
        ilastik_img_file = io._as_path_with_suffix(
            Path(ilastik_img_dir) / img_file.name, ".h5"
        )
        ilastik.write_ilastik_image(ilastik_img, ilastik_img_file)
        ilastik_img_files.append(ilastik_img_file)
        logger.info(ilastik_img_file)
        del ilastik_img
    Path(ilastik_crop_dir).mkdir(exist_ok=True)
    ilastik_crop_files = []
    for (
        ilastik_img_file,
        ilastik_crop_x,
        ilastik_crop_y,
        ilastik_crop,
    ) in ilastik.try_create_ilastik_crops_from_disk(
        ilastik_img_files, ilastik_crop_size, np.random.default_rng(seed=seed)
    ):
        if ilastik_crop is not None:
            ilastik_crop_file = Path(ilastik_crop_dir) / (
                f"{ilastik_img_file.stem}"
                f"_x{ilastik_crop_x}_y{ilastik_crop_y}"
                f"_w{ilastik_crop_size}_h{ilastik_crop_size}.h5"
            )
            ilastik.write_ilastik_crop(ilastik_crop, ilastik_crop_file)
            ilastik_crop_files.append(ilastik_crop_file)
            logger.info(ilastik_crop_file)
            del ilastik_crop
        else:
            logger.warning(f"Image {ilastik_img_file} too small for crop size")
    ilastik.create_and_save_ilastik_project(ilastik_crop_files, ilastik_project_file)
    logger.info(ilastik_project_file)


@ilastik_cmd_group.command(
    name="run", help="Run a pixel classification batch using Ilastik"
)
@click.option(
    "--ilastik",
    "ilastik_binary",
    type=click.STRING,
    default="/opt/ilastik/run_ilastik.sh",
    show_default=True,
    help="Ilastik binary",
)
@click.option(
    "--ilp",
    "ilastik_project_file",
    type=click.Path(exists=True, dir_okay=False),
    default="pixel_classifier.ilp",
    show_default=True,
    help="Path to the Ilastik project file",
)
@click.option(
    "--img",
    "ilastik_img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="ilastik_img",
    show_default=True,
    help="Path to the Ilastik image directory",
)
@click.option(
    "-o",
    "ilastik_probab_dir",
    type=click.Path(file_okay=False),
    default="ilastik_probabilities",
    show_default=True,
    help="Path to the Ilastik probabilities output directory",
)
@click.option(
    "--threads",
    "num_threads",
    type=click.IntRange(min=0),
    help="Maximum number of threads to use",
)
@click.option(
    "--mem",
    "memory_limit",
    type=click.IntRange(min=0),
    help="Memory limit (in megabytes)",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
@use_ilastik_env
def run_cmd(
    ilastik_binary,
    ilastik_project_file,
    ilastik_img_dir,
    ilastik_probab_dir,
    num_threads,
    memory_limit,
    ilastik_env,
):
    ilastik_img_files = ilastik.list_ilastik_image_files(ilastik_img_dir)
    Path(ilastik_probab_dir).mkdir(exist_ok=True)
    result = ilastik.run_pixel_classification(
        ilastik_binary,
        ilastik_project_file,
        ilastik_img_files,
        ilastik_probab_dir,
        num_threads=num_threads,
        memory_limit=memory_limit,
        ilastik_env=ilastik_env,
    )
    sys.exit(result.returncode)


@ilastik_cmd_group.command(
    name="fix", help="Fix existing Ilastik training data (experimental)"
)
@click.option(
    "--ilp",
    "ilastik_project_file",
    type=click.Path(exists=True, dir_okay=False),
    default="pixel_classifier.ilp",
    show_default=True,
    help="Path to the Ilastik project file",
)
@click.option(
    "--crop",
    "ilastik_crop_dir",
    type=click.Path(exists=True, file_okay=False),
    default="ilastik_crops",
    show_default=True,
    help="Path to the Ilastik crop directory",
)
@click.option(
    "--probabs",
    "ilastik_probab_dir",
    type=click.Path(file_okay=False),
    default="ilastik_probabilities",
    show_default=True,
    help="Path to the Ilastik probabilities directory",
)
@click.option(
    "--backup/--no-backup",
    "create_backup",
    default=True,
    show_default=True,
    help="Backup files before attempting to patch them",
)
@click.option(
    "--axisorder",
    "orig_axis_order",
    type=click.STRING,
    help="Axis order of the existing crops (e.g. zyxc)",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def fix_cmd(
    ilastik_project_file,
    ilastik_crop_dir,
    ilastik_probab_dir,
    create_backup,
    orig_axis_order,
):
    ilastik_crop_files = ilastik.list_ilastik_crop_files(ilastik_crop_dir)
    if create_backup:
        ilastik_project_backup_file = Path(ilastik_project_file).with_name(
            Path(ilastik_project_file).name + ".bak"
        )
        if ilastik_project_backup_file.exists():
            raise SteinbockCLIException("Ilastik project backup file exists")
        ilastik_crop_backup_dir = Path(ilastik_crop_dir).with_name(
            Path(ilastik_crop_dir).name + ".bak"
        )
        if ilastik_crop_backup_dir.exists():
            raise SteinbockCLIException("Ilastik crop backup directory exists")
        shutil.copyfile(ilastik_project_file, ilastik_project_backup_file)
        ilastik_crop_backup_dir.mkdir()
        for ilastik_crop_file in ilastik_crop_files:
            shutil.copyfile(
                ilastik_crop_file,
                ilastik_crop_backup_dir / ilastik_crop_file.name,
            )
    ilastik_crop_shapes = {}
    last_transpose_axes = None
    for (
        ilastik_crop_file,
        transpose_axes,
        ilastik_crop,
    ) in ilastik.try_fix_ilastik_crops_from_disk(
        ilastik_crop_files, orig_axis_order=orig_axis_order
    ):
        if last_transpose_axes not in (None, transpose_axes):
            raise SteinbockCLIException("Inconsistent axis orders across crops")
        ilastik.write_ilastik_crop(ilastik_crop, ilastik_crop_file)
        ilastik_crop_shapes[ilastik_crop_file.stem] = ilastik_crop.shape
        last_transpose_axes = transpose_axes
        logger.info(ilastik_crop_file)
        del ilastik_crop
    ilastik.fix_ilastik_project_file_inplace(
        ilastik_project_file,
        ilastik_crop_dir,
        ilastik_probab_dir,
        ilastik_crop_shapes,
        last_transpose_axes,
    )
    logger.info(ilastik_project_file)
