import click
import numpy as np
import shutil
import sys

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version, ilastik_binary, ilastik_env
from steinbock.classification.ilastik import ilastik

default_img_dir = "ilastik_img"
default_crop_dir = "ilastik_crops"
default_project_file = "pixel_classifier.ilp"
default_probabilities_dir = "ilastik_probabilities"


@click.group(
    name="ilastik",
    cls=cli.OrderedClickGroup,
    help="Perform supervised pixel classification using Ilastik",
)
def ilastik_cmd():
    pass


@ilastik_cmd.command(
    help="Prepare an Ilastik project file, images and crops",
)
@click.option(
    "--img",
    "src_img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image directory",
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
    "aggr_func_name",
    type=click.STRING,
    default="mean",
    show_default=True,
    help="Numpy function for aggregating channel pixels",
)
@click.option(
    "--dest",
    "project_file",
    type=click.Path(dir_okay=False),
    default=default_project_file,
    show_default=True,
    help="Path to the Ilastik project output file",
)
@click.option(
    "--imgdest",
    "img_dir",
    type=click.Path(file_okay=False),
    default=default_img_dir,
    show_default=True,
    help="Path to the Ilastik image output directory",
)
@click.option(
    "--cropdest",
    "crop_dir",
    type=click.Path(file_okay=False),
    default=default_crop_dir,
    show_default=True,
    help="Path to the Ilastik crop output directory",
)
@click.option(
    "--scale",
    "img_scale",
    type=click.INT,
    default=2,
    show_default=True,
    help="Ilastik image scale factor",
)
@click.option(
    "--cropsize",
    "crop_size",
    type=click.INT,
    default=512,
    show_default=True,
    help="Ilastik crop size (in pixels)",
)
@click.option(
    "--mean/--no-mean",
    "prepend_mean",
    default=True,
    show_default=True,
    help="Prepend mean of all channels as a new channel",
)
@click.option(
    "--seed",
    "seed",
    type=click.INT,
    help="Random seed",
)
@check_version
def prepare(
    src_img_dir,
    panel_file,
    aggr_func_name,
    project_file,
    img_dir,
    crop_dir,
    img_scale,
    crop_size,
    prepend_mean,
    seed,
):
    channel_groups = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if ilastik.panel_ilastik_col in panel:
            channel_groups = panel[ilastik.panel_ilastik_col].values
    aggr_func = getattr(np, aggr_func_name)
    img_files = []
    img_dir = Path(img_dir)
    img_dir.mkdir(exist_ok=True)
    for src_img_file, img in ilastik.create_images_from_disk(
        io.list_image_files(src_img_dir),
        channel_groups=channel_groups,
        aggr_func=aggr_func,
        prepend_mean=prepend_mean,
        img_scale=img_scale,
    ):
        img_file = ilastik.write_image(
            img,
            img_dir / f"{src_img_file.stem}",
            ilastik.img_dataset_path,
        )
        img_files.append(img_file)
        click.echo(img_file)
        del img
    crop_files = []
    crop_dir = Path(crop_dir)
    crop_dir.mkdir(exist_ok=True)
    for img_file, x_start, y_start, crop in ilastik.create_crops_from_disk(
        img_files,
        crop_size=crop_size,
        seed=seed,
    ):
        if crop is not None:
            crop_file_stem = (
                f"{img_file.stem}"
                f"_x{x_start}_y{y_start}"
                f"_w{crop_size}_h{crop_size}"
            )
            crop_file = ilastik.write_image(
                crop,
                crop_dir / crop_file_stem,
                ilastik.crop_dataset_path,
            )
            crop_files.append(crop_file)
            click.echo(crop_file)
            del crop
        else:
            click.echo(
                f"WARNING: Image {img_file} too small for crop size",
                file=sys.stderr,
            )
    ilastik.create_and_save_project(crop_files, project_file)


@ilastik_cmd.command(
    help="Run a pixel classification batch using Ilastik",
)
@click.option(
    "--ilp",
    "project_file",
    type=click.Path(exists=True, dir_okay=False),
    default=default_project_file,
    show_default=True,
    help="Path to the Ilastik project file",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=default_img_dir,
    show_default=True,
    help="Path to the Ilastik image directory",
)
@click.option(
    "--dest",
    "probabilities_dir",
    type=click.Path(file_okay=False),
    default=default_probabilities_dir,
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
@check_version
@ilastik_env
def run(
    project_file,
    img_dir,
    probabilities_dir,
    num_threads,
    memory_limit,
    env,
):
    Path(probabilities_dir).mkdir(exist_ok=True)
    result = ilastik.run_pixel_classification(
        ilastik_binary,
        project_file,
        ilastik.list_image_files(img_dir),
        probabilities_dir,
        num_threads=num_threads,
        memory_limit=memory_limit,
        ilastik_env=env,
    )
    sys.exit(result.returncode)


@ilastik_cmd.command(
    help="Fix existing Ilastik training data (experimental)",
)
@click.option(
    "--ilp",
    "project_file",
    type=click.Path(exists=True, dir_okay=False),
    default=default_project_file,
    show_default=True,
    help="Path to the Ilastik project file",
)
@click.option(
    "--crops",
    "crop_dir",
    type=click.Path(exists=True, file_okay=False),
    default=default_crop_dir,
    show_default=True,
    help="Path to the Ilastik crop directory",
)
@click.option(
    "--probab",
    "probabilities_dir",
    type=click.Path(file_okay=False),
    default=default_probabilities_dir,
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
    "axis_order",
    type=click.STRING,
    help="Axis order of the existing crops (e.g., zyxc)",
)
@check_version
def fix(
    project_file,
    crop_dir,
    probabilities_dir,
    create_backup,
    axis_order,
):
    project_file = Path(project_file)
    crop_dir = Path(crop_dir)
    if create_backup:
        project_bak_file = project_file.with_name(project_file.name + ".bak")
        if project_bak_file.exists():
            return click.echo(
                "ERROR: Ilastik project backup file exists",
                file=sys.stderr,
            )
        crop_bak_dir = crop_dir.with_name(crop_dir.name + ".bak")
        if crop_bak_dir.exists():
            return click.echo(
                "ERROR: Ilastik crop backup directory exists",
                file=sys.stderr,
            )
        shutil.copyfile(project_file, project_bak_file)
        crop_bak_dir.mkdir()
        for crop_file in ilastik.list_crop_files(crop_dir):
            shutil.copyfile(crop_file, crop_bak_dir / crop_file.name)
    crop_shapes = {}
    last_transpose_axes = None
    for crop_file, transpose_axes, crop in ilastik.read_and_fix_crops(
        ilastik.list_crop_files(crop_dir),
        axis_order=axis_order,
    ):
        if last_transpose_axes not in (None, transpose_axes):
            return click.echo(
                "ERROR: Inconsistent axis orders across crops",
                file=sys.stderr,
            )
        crop_file = ilastik.write_image(
            crop,
            crop_file,
            ilastik.crop_dataset_path,
        )
        crop_shapes[crop_file.stem] = crop.shape
        last_transpose_axes = transpose_axes
        click.echo(crop_file)
        del crop
    ilastik.fix_project_file_inplace(
        project_file,
        crop_dir,
        probabilities_dir,
        crop_shapes,
        last_transpose_axes,
    )
