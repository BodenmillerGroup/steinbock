import click
import os
import shutil
import sys

from pathlib import Path

from steinbock import cli, io
from steinbock._env import (
    cellprofiler_binary,
    cellprofiler_plugin_dir,
    check_version,
)
from steinbock.measurement.cellprofiler import cellprofiler

default_measurement_pipeline_file = "cell_measurement.cppipe"
default_input_dir = "cellprofiler_input"
default_output_dir = "cellprofiler_output"


@click.group(
    name="cellprofiler",
    cls=cli.OrderedClickGroup,
    help="Run a CellProfiler measurement pipeline (legacy)",
)
def cellprofiler_cmd():
    pass


@cellprofiler_cmd.command(
    help="Prepare a CellProfiler measurement pipeline",
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
    "--masks",
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
    "--dest",
    "measurement_pipeline_file",
    type=click.Path(dir_okay=False),
    default=default_measurement_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler measurement pipeline output file",
)
@click.option(
    "--destdir",
    "input_dir",
    type=click.Path(file_okay=False),
    default=default_input_dir,
    show_default=True,
    help="Path to the CellProfiler input directory",
)
@click.option(
    "--symlinks/--no-symlinks",
    "use_symlinks",
    default=False,
    show_default=True,
    help="Use symbolic links instead of copying files",
)
@check_version
def prepare(
    img_dir,
    mask_dir,
    panel_file,
    measurement_pipeline_file,
    input_dir,
    use_symlinks,
):
    panel = io.read_panel(panel_file)
    num_channels = len(panel.index)
    img_files = io.list_images(img_dir)
    mask_files = io.list_masks(mask_dir)
    input_dir = Path(input_dir)
    input_dir.mkdir(exist_ok=True)
    for img_file, mask_file in zip(img_files, mask_files):
        img_name = img_file.name
        mask_name = f"{mask_file.stem}_mask{mask_file.suffix}"
        if use_symlinks:
            os.symlink(img_file, input_dir / img_name)
            os.symlink(mask_file, input_dir / mask_name)
        else:
            shutil.copyfile(img_file, input_dir / img_name)
            shutil.copyfile(mask_file, input_dir / mask_name)
    cellprofiler.create_measurement_pipeline(
        measurement_pipeline_file,
        num_channels,
    )


@cellprofiler_cmd.command(
    help="Run an object measurement batch using CellProfiler",
)
@click.option(
    "--pipe",
    "measurement_pipeline_file",
    type=click.Path(exists=True, dir_okay=False),
    default=default_measurement_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler measurement pipeline file",
)
@click.option(
    "--input",
    "input_dir",
    type=click.Path(exists=True, file_okay=False),
    default=default_input_dir,
    show_default=True,
    help="Path to the CellProfiler input directory",
)
@click.option(
    "--dest",
    "output_dir",
    type=click.Path(file_okay=False),
    default=default_output_dir,
    show_default=True,
    help="Path to the CellProfiler output directory",
)
@check_version
def run(
    measurement_pipeline_file,
    input_dir,
    output_dir,
):
    Path(output_dir).mkdir(exist_ok=True)
    result = cellprofiler.measure_objects(
        cellprofiler_binary,
        measurement_pipeline_file,
        input_dir,
        output_dir,
        cellprofiler_plugin_dir=cellprofiler_plugin_dir,
    )
    sys.exit(result.returncode)
