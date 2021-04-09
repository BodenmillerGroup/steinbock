import click
import os
import shutil
import sys

from pathlib import Path

from steinbock.measurement.cellprofiler.cellprofiler import (
    create_measurement_pipeline,
    measure_cells,
)
from steinbock.utils import cli, io

cellprofiler_binary = "cellprofiler"
cellprofiler_plugin_dir = "/opt/cellprofiler_plugins"

default_measurement_pipeline_file = "cell_measurement.cppipe"
default_cellprofiler_input_dir = "cellprofiler_input"
default_cellprofiler_output_dir = "cellprofiler_output"


@click.group(
    cls=cli.OrderedClickGroup,
    help="Run legacy CellProfiler measurement pipeline",
)
def cellprofiler():
    pass


@cellprofiler.command(
    name="prepare",
    help="Prepare a CellProfiler measurement pipeline",
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
    "--masks",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask .tiff directory",
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
    "measurement_pipeline_file",
    type=click.Path(dir_okay=False),
    default=default_measurement_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler measurement pipeline output file",
)
@click.option(
    "--destdir",
    "cellprofiler_input_dir",
    type=click.Path(file_okay=False),
    default=default_cellprofiler_input_dir,
    show_default=True,
    help="Path to the CellProfiler input directory",
)
@click.option(
    "--symlink/--no-symlink",
    "use_symlinks",
    default=False,
    show_default=True,
    help="Use symbolic links instead of copying files",
)
def prepare_measure(
    img_dir,
    mask_dir,
    panel_file,
    measurement_pipeline_file,
    cellprofiler_input_dir,
    use_symlinks,
):
    num_channels = len(io.read_panel(panel_file).index)
    cellprofiler_input_dir = Path(cellprofiler_input_dir)
    cellprofiler_input_dir.mkdir(exist_ok=True)
    img_files = sorted(Path(img_dir).glob("*.tiff"))
    mask_files = sorted(Path(mask_dir).glob("*.tiff"))
    for img_file, mask_file in zip(img_files, mask_files):
        img_name = img_file.name
        mask_name = f"{mask_file.stem}_mask.tiff"
        if use_symlinks:
            os.symlink(img_file, cellprofiler_input_dir / img_name)
            os.symlink(mask_file, cellprofiler_input_dir / mask_name)
        else:
            shutil.copyfile(img_file, cellprofiler_input_dir / img_name)
            shutil.copyfile(mask_file, cellprofiler_input_dir / mask_name)
    create_measurement_pipeline(measurement_pipeline_file, num_channels)


@cellprofiler.command(
    name="run-measure",
    help="Run cell measurement batch using CellProfiler",
)
@click.option(
    "--pipe",
    "measurement_pipeline_file",
    type=click.Path(exists=True, dir_okay=False),
    default=default_measurement_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler measurement pipeline .cppipe file",
)
@click.option(
    "--input",
    "cellprofiler_input_dir",
    type=click.Path(exists=True, file_okay=False),
    default=default_cellprofiler_input_dir,
    show_default=True,
    help="Path to the CellProfiler input directory",
)
@click.option(
    "--dest",
    "cellprofiler_output_dir",
    type=click.Path(file_okay=False),
    default=default_cellprofiler_output_dir,
    show_default=True,
    help="Path to the CellProfiler output directory",
)
def run_measure(
    measurement_pipeline_file,
    cellprofiler_input_dir,
    cellprofiler_output_dir,
):
    Path(cellprofiler_output_dir).mkdir(exist_ok=True)
    result = measure_cells(
        cellprofiler_binary,
        measurement_pipeline_file,
        cellprofiler_input_dir,
        cellprofiler_output_dir,
        cellprofiler_plugin_dir=cellprofiler_plugin_dir,
    )
    sys.exit(result.returncode)
