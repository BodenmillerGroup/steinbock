import sys
from pathlib import Path

import click
import click_log
import numpy as np
import tifffile

from ... import io
from ..._cli.utils import OrderedClickGroup, catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import cellprofiler


@click.group(
    name="cellprofiler",
    cls=OrderedClickGroup,
    help="Run a CellProfiler measurement pipeline (legacy)",
)
def cellprofiler_cmd_group():
    pass


@cellprofiler_cmd_group.command(
    name="prepare", help="Prepare a CellProfiler measurement pipeline"
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
    "--masks",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
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
    "--pipeout",
    "measurement_pipeline_file",
    type=click.Path(dir_okay=False),
    default="cell_measurement.cppipe",
    show_default=True,
    help="Path to the CellProfiler measurement pipeline output file",
)
@click.option(
    "--dataout",
    "cpdata_dir",
    type=click.Path(file_okay=False),
    default="cellprofiler_input",
    show_default=True,
    help="Path to the CellProfiler input directory",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def prepare_cmd(
    img_dir,
    mask_dir,
    panel_file,
    measurement_pipeline_file,
    cpdata_dir,
):
    panel = io.read_panel(panel_file)
    img_files = io.list_image_files(img_dir)
    mask_files = io.list_mask_files(mask_dir, base_files=img_files)
    Path(cpdata_dir).mkdir(exist_ok=True)
    for img_file, mask_file in zip(img_files, mask_files):
        img = io.read_image(img_file, native_dtype=True)
        cp_img_file = Path(cpdata_dir) / img_file.name
        tifffile.imwrite(
            cp_img_file,
            data=io._to_dtype(img, np.uint16)[
                np.newaxis, np.newaxis, :, :, :, np.newaxis
            ],
            imagej=True,
        )
        logger.info(cp_img_file)
        del img
        mask = io.read_mask(mask_file, native_dtype=True)
        cp_mask_file = Path(cpdata_dir) / f"{mask_file.stem}_mask{mask_file.suffix}"
        tifffile.imwrite(
            cp_mask_file,
            data=io._to_dtype(mask, np.uint16)[
                np.newaxis, np.newaxis, np.newaxis, :, :, np.newaxis
            ],
            imagej=True,
        )
        logger.info(cp_mask_file)
        del mask
    cellprofiler.create_and_save_measurement_pipeline(
        measurement_pipeline_file, len(panel.index)
    )
    logger.info(measurement_pipeline_file)


@cellprofiler_cmd_group.command(
    name="run", help="Run an object measurement batch using CellProfiler"
)
@click.option(
    "--cellprofiler",
    "cellprofiler_binary",
    type=click.STRING,
    default="cellprofiler",
    show_default=True,
    help="CellProfiler binary",
)
@click.option(
    "--plugins-directory",
    "cellprofiler_plugin_dir",
    type=click.Path(file_okay=False),
    default="/opt/cellprofiler_plugins",
    show_default=True,
    help="Path to the CellProfiler plugin directory",
)
@click.option(
    "--pipe",
    "measurement_pipeline_file",
    type=click.Path(exists=True, dir_okay=False),
    default="cell_measurement.cppipe",
    show_default=True,
    help="Path to the CellProfiler measurement pipeline file",
)
@click.option(
    "--data",
    "cpdata_dir",
    type=click.Path(exists=True, file_okay=False),
    default="cellprofiler_input",
    show_default=True,
    help="Path to the CellProfiler input directory",
)
@click.option(
    "-o",
    "cpout_dir",
    type=click.Path(file_okay=False),
    default="cellprofiler_output",
    show_default=True,
    help="Path to the CellProfiler output directory",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def run_cmd(
    cellprofiler_binary,
    cellprofiler_plugin_dir,
    measurement_pipeline_file,
    cpdata_dir,
    cpout_dir,
):
    Path(cpout_dir).mkdir(exist_ok=True)
    result = cellprofiler.try_measure_objects(
        cellprofiler_binary,
        measurement_pipeline_file,
        cpdata_dir,
        cpout_dir,
        cellprofiler_plugin_dir=cellprofiler_plugin_dir,
    )
    sys.exit(result.returncode)
