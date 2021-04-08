import click
import numpy as np
import os
import shutil
import sys

from pathlib import Path

from steinbock.classification.ilastik.ilastik import (
    create_ilastik_images,
    create_ilastik_patches,
    create_ilastik_project,
    fix_patches_and_project_inplace,
    classify_pixels,
)
from steinbock.utils import cli, io, system

ilastik_binary = "/opt/ilastik/run_ilastik.sh"
ilastik_panel_col = "ilastik"

default_ilastik_img_dir = "ilastik_img"
default_ilastik_patch_dir = "ilastik_patches"
default_ilastik_project_file = "pixel_classifier.ilp"
default_ilastik_probab_dir = "ilastik_probabilities"


@click.group(
    cls=cli.OrderedClickGroup,
    help="Perform supervised pixel classification using Ilastik",
)
def ilastik():
    pass


@ilastik.command(
    help="Prepare Ilastik images, patches and project file",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image .tiff directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default=cli.default_panel_file,
    show_default=True,
    help="Path to the panel .csv file",
)
@click.option(
    "--dest",
    "ilastik_project_file",
    type=click.Path(dir_okay=False),
    default=default_ilastik_project_file,
    show_default=True,
    help="Path to the Ilastik project output file",
)
@click.option(
    "--imgdest",
    "ilastik_img_dir",
    type=click.Path(file_okay=False),
    default=default_ilastik_img_dir,
    show_default=True,
    help="Path to the Ilastik image output directory",
)
@click.option(
    "--patchdest",
    "ilastik_patch_dir",
    type=click.Path(file_okay=False),
    default=default_ilastik_patch_dir,
    show_default=True,
    help="Path to the Ilastik patch output directory",
)
@click.option(
    "--imgscale",
    "img_scale",
    type=click.INT,
    default=2,
    show_default=True,
    help="Ilastik image scale factor",
)
@click.option(
    "--patchsize",
    "patch_size",
    type=click.INT,
    default=512,
    show_default=True,
    help="Ilastik patch size (in pixels)",
)
@click.option(
    "--seed",
    "seed",
    type=click.INT,
    required=True,
    help="Random seed",
)
def prepare(
    img_dir,
    panel_file,
    ilastik_project_file,
    ilastik_img_dir,
    ilastik_patch_dir,
    img_scale,
    patch_size,
    seed,
):
    img_files = sorted(Path(img_dir).glob("*.tiff"))
    channel_indices = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if ilastik_panel_col in panel:
            channel_indices = np.flatnonzero(panel[ilastik_panel_col].values)
    Path(ilastik_img_dir).mkdir(exist_ok=True)
    ilastik_img_files = create_ilastik_images(
        img_files,
        ilastik_img_dir,
        img_scale=img_scale,
        channel_indices=channel_indices,
    )
    Path(ilastik_patch_dir).mkdir(exist_ok=True)
    ilastik_patch_files = create_ilastik_patches(
        ilastik_img_files,
        ilastik_patch_dir,
        patch_size=patch_size,
        seed=seed,
    )
    create_ilastik_project(ilastik_patch_files, ilastik_project_file)


@ilastik.command(
    context_settings={"ignore_unknown_options": True},
    help="Run Ilastik application (GUI mode requires X11)",
    add_help_option=False,
)
@click.argument(
    "ilastik_args",
    nargs=-1,
    type=click.UNPROCESSED,
)
def app(ilastik_args):
    x11_warning_message = system.check_x11()
    if x11_warning_message is not None:
        click.echo(x11_warning_message, file=sys.stderr)
    args = [ilastik_binary] + list(ilastik_args)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    result = system.run_captured(args, env=env)
    sys.exit(result.returncode)


@ilastik.command(
    help="Run pixel classification batch using Ilastik",
)
@click.option(
    "--ilp",
    "ilastik_project_file",
    type=click.Path(exists=True, dir_okay=False),
    default=default_ilastik_project_file,
    show_default=True,
    help="Path to the Ilastik project .ilp file",
)
@click.option(
    "--img",
    "ilastik_img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=default_ilastik_img_dir,
    show_default=True,
    help="Path to the Ilastik image .h5 directory",
)
@click.option(
    "--dest",
    "ilastik_probab_dir",
    type=click.Path(file_okay=False),
    default=default_ilastik_probab_dir,
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
def run(
    ilastik_project_file,
    ilastik_img_dir,
    ilastik_probab_dir,
    num_threads,
    memory_limit,
):
    ilastik_img_files = sorted(Path(ilastik_img_dir).glob("*.h5"))
    Path(ilastik_probab_dir).mkdir(exist_ok=True)
    result = classify_pixels(
        ilastik_binary,
        ilastik_project_file,
        ilastik_img_files,
        ilastik_probab_dir,
        num_threads=num_threads,
        memory_limit=memory_limit,
    )
    sys.exit(result.returncode)


@ilastik.command(
    help="Fix existing Ilastik training data (experimental)",
)
@click.option(
    "--ilp",
    "ilastik_project_file",
    type=click.Path(exists=True, dir_okay=False),
    default=default_ilastik_project_file,
    show_default=True,
    help="Path to the Ilastik project .ilp file",
)
@click.option(
    "--patch",
    "ilastik_patch_dir",
    type=click.Path(exists=True, file_okay=False),
    default=default_ilastik_patch_dir,
    show_default=True,
    help="Path to the Ilastik patch .h5 directory",
)
@click.option(
    "--probab",
    "ilastik_probab_dir",
    type=click.Path(file_okay=False),
    default=default_ilastik_probab_dir,
    show_default=True,
    help="Path to the Ilastik probabilities .tiff directory",
)
@click.option(
    "--axisorder",
    "axis_order",
    type=click.STRING,
    help="Axis order of the existing patches (e.g., zyxc)",
)
def fix(
    ilastik_project_file,
    ilastik_patch_dir,
    ilastik_probab_dir,
    axis_order,
):
    ilastik_project_file = Path(ilastik_project_file)
    ilastik_patch_dir = Path(ilastik_patch_dir)
    ilastik_project_backup_file = ilastik_project_file.with_name(
        ilastik_project_file.name + ".bak"
    )
    if ilastik_project_backup_file.exists():
        click.echo("Existing Ilastik project backup file", file=sys.stdout)
        return
    ilastik_patch_backup_dir = ilastik_patch_dir.with_name(
        ilastik_patch_dir.name + ".bak"
    )
    if ilastik_patch_backup_dir.exists():
        click.echo("Existing Ilastik patch backup directory", file=sys.stdout)
        return
    shutil.copyfile(ilastik_project_file, ilastik_project_backup_file)
    ilastik_patch_backup_dir.mkdir()
    for ilastik_patch_file in sorted(ilastik_patch_dir.glob("*.h5")):
        shutil.copyfile(
            ilastik_patch_file,
            ilastik_patch_backup_dir / ilastik_patch_file.name,
        )
    fix_patches_and_project_inplace(
        ilastik_project_file,
        ilastik_patch_dir,
        ilastik_probab_dir,
        axis_order=axis_order,
    )
