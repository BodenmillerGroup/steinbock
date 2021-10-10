from os import PathLike
from pathlib import Path
from typing import Union

from steinbock._env import run_captured

_measurement_pipeline_file_template = (
    Path(__file__).parent / "data" / "cell_measurement.cppipe"
)


def create_and_save_measurement_pipeline(
    measurement_pipeline_file: Union[str, PathLike], num_channels: int
):
    with _measurement_pipeline_file_template.open(mode="r") as f:
        s = f.read()
    s = s.replace("{{NUM_CHANNELS}}", str(num_channels))
    with Path(measurement_pipeline_file).open(mode="w") as f:
        f.write(s)


def try_measure_objects(
    cellprofiler_binary: str,
    measurement_pipeline_file: Union[str, PathLike],
    cpdata_dir: Union[str, PathLike],
    cpout_dir: Union[str, PathLike],
    cellprofiler_plugin_dir: Union[str, PathLike, None] = None,
):
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
    if cellprofiler_plugin_dir is not None:
        args.append("--plugins-directory")
        args.append(str(cellprofiler_plugin_dir))
    return run_captured(args)
