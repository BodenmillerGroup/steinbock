import pytest
import shutil

from pathlib import Path

from steinbock._env import cellprofiler_binary, cellprofiler_plugin_dir
from steinbock.measurement import cellprofiler


class TestCellprofilerMeasurement:
    def test_create_and_save_measurement_pipeline(self, tmp_path: Path):
        cellprofiler.create_and_save_measurement_pipeline(
            tmp_path / "cell_measurement.cppipe", 5
        )  # TODO

    @pytest.mark.skip(reason="Test would take too long")
    @pytest.mark.skipif(
        shutil.which(cellprofiler_binary) is None,
        reason="CellProfiler is not available",
    )
    def test_try_measure_objects(
        self, imc_test_data_steinbock_path: Path, tmp_path: Path
    ):
        cellprofiler.try_measure_objects(
            cellprofiler_binary,
            imc_test_data_steinbock_path / "cell_measurement.cppipe",
            imc_test_data_steinbock_path / "cellprofiler_input",
            tmp_path / "cellprofiler_output",
            cellprofiler_plugin_dir=cellprofiler_plugin_dir,
        )  # TODO
