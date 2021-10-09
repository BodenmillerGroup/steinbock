import shutil

from os import PathLike
from pathlib import Path
from typing import Union

from steinbock._env import run_captured

_segmentation_pipeline_file_template = (
    Path(__file__).parent / "data" / "cell_segmentation.cppipe"
)


def create_and_save_segmentation_pipeline(
    segmentation_pipeline_file: Union[str, PathLike]
):
    shutil.copyfile(
        _segmentation_pipeline_file_template, segmentation_pipeline_file
    )


def try_segment_objects(
    cellprofiler_binary: Union[str, PathLike],
    segmentation_pipeline_file: Union[str, PathLike],
    probabilities_dir: Union[str, PathLike],
    mask_dir: Union[str, PathLike],
    cellprofiler_plugin_dir: Union[str, PathLike, None] = None,
):
    args = [
        str(cellprofiler_binary),
        "-c",
        "-r",
        "-p",
        str(segmentation_pipeline_file),
        "-i",
        str(probabilities_dir),
        "-o",
        str(mask_dir),
    ]
    if cellprofiler_plugin_dir is not None:
        args.append("--plugins-directory")
        args.append(str(cellprofiler_plugin_dir))
    return run_captured(args)
