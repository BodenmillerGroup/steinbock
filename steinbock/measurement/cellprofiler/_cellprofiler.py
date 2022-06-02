import subprocess
from importlib import resources
from os import PathLike
from pathlib import Path
from typing import Union

from ..._env import run_captured
from . import data as cellprofiler_data


def create_and_save_measurement_pipeline(
    measurement_pipeline_file: Union[str, PathLike], num_channels: int
) -> None:
    s = resources.read_text(cellprofiler_data, "cell_measurement.cppipe")
    s = s.replace("{{NUM_CHANNELS}}", str(num_channels))
    with Path(measurement_pipeline_file).open(mode="w") as f:
        f.write(s)


def try_measure_objects(
    cellprofiler_binary: str,
    measurement_pipeline_file: Union[str, PathLike],
    cpdata_dir: Union[str, PathLike],
    cpout_dir: Union[str, PathLike],
    cellprofiler_plugin_dir: Union[str, PathLike, None] = None,
) -> subprocess.CompletedProcess:
    args = [
        cellprofiler_binary,
        "-c",
        "-r",
        "-p",
        str(measurement_pipeline_file),
        "-i",
        str(cpdata_dir),
        "-o",
        str(cpout_dir),
    ]
    if cellprofiler_plugin_dir is not None and Path(cellprofiler_plugin_dir).exists():
        args.append(f"--plugins-directory={cellprofiler_plugin_dir}")
    return run_captured(args)
