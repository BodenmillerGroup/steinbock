import pytest
import shutil

from pathlib import Path

from steinbock._env import cellprofiler_binary, cellprofiler_plugin_dir
from steinbock.segmentation import cellprofiler


class TestCellprofilerSegmentation:
    def test_create_and_save_segmentation_pipeline(self, tmp_path: Path):
        cellprofiler.create_and_save_segmentation_pipeline(
            tmp_path / "cell_segmentation.cppipe"
        )  # TODO

    @pytest.mark.skip(reason="Test would take too long")
    @pytest.mark.skipif(
        shutil.which(cellprofiler_binary) is None,
        reason="CellProfiler is not available",
    )
    def test_try_segment_objects(
        self, imc_test_data_steinbock_path: Path, tmp_path: Path
    ):
        cellprofiler.try_segment_objects(
            cellprofiler_binary,
            imc_test_data_steinbock_path / "cell_segmentation.cppipe",
            imc_test_data_steinbock_path / "ilastik_probabilities",
            tmp_path / "masks",
            cellprofiler_plugin_dir=cellprofiler_plugin_dir,
        )  # TODO
