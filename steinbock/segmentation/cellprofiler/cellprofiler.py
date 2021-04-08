import shutil

from os import PathLike
from pathlib import Path
from typing import Union

from steinbock.utils import system

_data_dir = Path(__file__).parent / "data"
_segmentation_pipeline_file_template = _data_dir / "cell_segmentation.cppipe"
_measurement_pipeline_file_template = _data_dir / "cell_measurement.cppipe"


def create_segmentation_pipeline(
    segmentation_pipeline_file: Union[str, PathLike],
):
    segmentation_pipeline_file = Path(segmentation_pipeline_file)
    shutil.copyfile(
        _segmentation_pipeline_file_template,
        segmentation_pipeline_file,
    )


def create_measurement_pipeline(
    measurement_pipeline_file: Union[str, PathLike],
    num_channels: int,
):
    measurement_pipeline_file = Path(measurement_pipeline_file)
    with _measurement_pipeline_file_template.open(mode='r') as f:
        s = f.read()
    s = s.replace("{{NUM_CHANNELS}}", str(num_channels))
    with measurement_pipeline_file.open(mode="w") as f:
        f.write(s)


def segment_cells(
    cellprofiler_binary: str,
    segmentation_pipeline_file: Union[str, PathLike],
    probab_dir: Union[str, PathLike],
    mask_dir: Union[str, PathLike],
    cellprofiler_plugin_dir: Union[str, PathLike, None] = None,
):
    args = [
        cellprofiler_binary,
        "-c",
        "-r",
        "-p",
        str(segmentation_pipeline_file),
        "-i",
        str(probab_dir),
        "-o",
        str(mask_dir),
    ]
    if cellprofiler_plugin_dir is not None:
        args.append("--plugins-directory")
        args.append(str(cellprofiler_plugin_dir))
    return system.run_captured(args)


def measure_cells(
    cellprofiler_binary: str,
    measurement_pipeline_file: Union[str, PathLike],
    cellprofiler_input_dir: Union[str, PathLike],
    cellprofiler_output_dir: Union[str, PathLike],
    cellprofiler_plugin_dir: Union[str, PathLike, None] = None,
):
    args = [
        cellprofiler_binary,
        "-c",
        "-r",
        "-p",
        str(measurement_pipeline_file),
        "-i",
        str(cellprofiler_input_dir),
        "-o",
        str(cellprofiler_output_dir),
    ]
    if cellprofiler_plugin_dir is not None:
        args.append("--plugins-directory")
        args.append(str(cellprofiler_plugin_dir))
    return system.run_captured(args)
