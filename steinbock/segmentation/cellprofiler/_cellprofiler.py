import shutil
import subprocess
from importlib import resources
from os import PathLike
from pathlib import Path
from typing import Union

from ..._env import run_captured
from . import data as cellprofiler_data


def create_and_save_segmentation_pipeline(
    segmentation_pipeline_file: Union[str, PathLike]
) -> None:
    with resources.open_binary(cellprofiler_data, "cell_segmentation.cppipe") as fsrc:
        with open(segmentation_pipeline_file, mode="wb") as fdst:
            shutil.copyfileobj(fsrc, fdst)


def try_segment_objects(
    python_path: str,
    cellprofiler_module: str,
    segmentation_pipeline_file: Union[str, PathLike],
    probabilities_dir: Union[str, PathLike],
    mask_dir: Union[str, PathLike],
    cellprofiler_plugin_dir: Union[str, PathLike, None] = None,
) -> subprocess.CompletedProcess:
    args = [
        python_path,
        "-m",
        cellprofiler_module,
        "-c",
        "-r",
        "-p",
        str(segmentation_pipeline_file),
        "-i",
        str(probabilities_dir),
        "-o",
        str(mask_dir),
    ]
    if cellprofiler_plugin_dir is not None and Path(cellprofiler_plugin_dir).is_dir():
        args.append(f"--plugins-directory={cellprofiler_plugin_dir}")
    return run_captured(args)
