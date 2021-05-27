import click
import sys

from pathlib import Path

from steinbock import cli
from steinbock._env import (
    cellprofiler_binary,
    cellprofiler_plugin_dir,
    check_version,
)
from steinbock.segmentation.cellprofiler import cellprofiler

default_segmentation_pipeline_file = "cell_segmentation.cppipe"


@click.group(
    name="cellprofiler",
    cls=cli.OrderedClickGroup,
    help="Segment objects in probability images using CellProfiler",
)
def cellprofiler_cmd():
    pass


@cellprofiler_cmd.command(
    help="Prepare a CellProfiler segmentation pipeline",
)
@click.option(
    "--dest",
    "segmentation_pipeline_file",
    type=click.Path(dir_okay=False),
    default=default_segmentation_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler segmentation pipeline output file",
)
@check_version
def prepare(segmentation_pipeline_file):
    cellprofiler.create_and_save_segmentation_pipeline(
        segmentation_pipeline_file
    )


@cellprofiler_cmd.command(
    help="Run a object segmentation batch using CellProfiler",
)
@click.option(
    "--pipe",
    "segmentation_pipeline_file",
    type=click.Path(exists=True, dir_okay=False),
    default=default_segmentation_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler segmentation pipeline file",
)
@click.option(
    "--probab",
    "probabilities_dir",
    type=click.Path(exists=True, file_okay=False),
    default="ilastik_probabilities",
    show_default=True,
    help="Path to the probabilities directory",
)
@click.option(
    "--dest",
    "mask_dir",
    type=click.Path(file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask output directory",
)
@check_version
def run(
    segmentation_pipeline_file,
    probabilities_dir,
    mask_dir,
):
    if probabilities_dir not in ("ilastik_probabilities",):
        click.echo(
            "WARNING: When using custom probabilities from unknown origins, "
            "make sure to adapt the CellProfiler pipeline accordingly",
            file=sys.stderr,
        )
    Path(mask_dir).mkdir(exist_ok=True)
    result = cellprofiler.run_object_segmentation(
        cellprofiler_binary,
        segmentation_pipeline_file,
        probabilities_dir,
        mask_dir,
        cellprofiler_plugin_dir=cellprofiler_plugin_dir,
    )
    sys.exit(result.returncode)
