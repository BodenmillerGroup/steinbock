import click
import os
import shutil
import sys

from pathlib import Path

from steinbock.segmentation.cellprofiler.cellprofiler import (
    create_segmentation_pipeline,
    create_measurement_pipeline,
    segment_cells,
    measure_cells,
)
from steinbock.utils import cli, io, system


cellprofiler_binary = "cellprofiler"
cellprofiler_plugin_dir = "/opt/cellprofiler_plugins"

_default_segmentation_pipeline_file = "cell_segmentation.cppipe"
_default_measurement_pipeline_file = "cell_measurement.cppipe"
_default_cellprofiler_input_dir = "cellprofiler_input"
_default_cellprofiler_output_dir = "cellprofiler_output"


@click.group(
    cls=cli.OrderedClickGroup,
    help="Perform cell segmentation using a CellProfiler pipeline",
)
def cellprofiler():
    pass


@cellprofiler.command(
    help="Prepare a CellProfiler segmentation pipeline",
)
@click.option(
    "--dest",
    "segmentation_pipeline_file",
    type=click.Path(dir_okay=False),
    default=_default_segmentation_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler segmentation pipeline output file",
)
def prepare(segmentation_pipeline_file):
    create_segmentation_pipeline(segmentation_pipeline_file)


@cellprofiler.command(
    context_settings={"ignore_unknown_options": True},
    help="Run CellProfiler application (GUI mode requires X11)",
    add_help_option=False,
)
@click.argument(
    "cellprofiler_args",
    nargs=-1,
    type=click.UNPROCESSED,
)
def app(cellprofiler_args):
    x11_warning_message = system.check_x11()
    if x11_warning_message is not None:
        click.echo(x11_warning_message, file=sys.stderr)
    args = [cellprofiler_binary] + list(cellprofiler_args)
    if not any(arg.startswith("--plugins-directory") for arg in args):
        args.append(f"--plugins-directory={cellprofiler_plugin_dir}")
    result = system.run_captured(args)
    sys.exit(result.returncode)


@cellprofiler.command(
    help="Run cell segmentation batch using CellProfiler",
)
@click.option(
    "--pipe",
    "segmentation_pipeline_file",
    type=click.Path(exists=True, dir_okay=False),
    default=_default_segmentation_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler segmentation pipeline .cppipe file",
)
@click.option(
    "--probab",
    "probab_dir",
    type=click.Path(exists=True, file_okay=False),
    default="ilastik_probabilities",
    show_default=True,
    help="Path to the probabilities .tiff directory",
)
@click.option(
    "--dest",
    "mask_dir",
    type=click.Path(file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask output directory",
)
def run(
    segmentation_pipeline_file,
    probab_dir,
    mask_dir,
):
    if probab_dir not in ("ilastik_probabilities",):
        click.echo(
            "When using probabilities originating from unknown sources, "
            "make sure to adapt the CellProfiler pipeline accordingly",
            file=sys.stderr,
        )
    Path(mask_dir).mkdir(exist_ok=True)
    result = segment_cells(
        cellprofiler_binary,
        segmentation_pipeline_file,
        probab_dir,
        mask_dir,
        cellprofiler_plugin_dir=cellprofiler_plugin_dir,
    )
    sys.exit(result.returncode)


@cellprofiler.command(
    name="prepare-measure",
    help="Prepare a CellProfiler measurement pipeline (legacy)",
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
    default=_default_measurement_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler measurement pipeline output file",
)
@click.option(
    "--destdir",
    "cellprofiler_input_dir",
    type=click.Path(file_okay=False),
    default=_default_cellprofiler_input_dir,
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
    help="Run cell measurement batch using CellProfiler (legacy)",
)
@click.option(
    "--pipe",
    "measurement_pipeline_file",
    type=click.Path(exists=True, dir_okay=False),
    default=_default_measurement_pipeline_file,
    show_default=True,
    help="Path to the CellProfiler measurement pipeline .cppipe file",
)
@click.option(
    "--input",
    "cellprofiler_input_dir",
    type=click.Path(exists=True, file_okay=False),
    default=_default_cellprofiler_input_dir,
    show_default=True,
    help="Path to the CellProfiler input directory",
)
@click.option(
    "--dest",
    "cellprofiler_output_dir",
    type=click.Path(file_okay=False),
    default=_default_cellprofiler_output_dir,
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
