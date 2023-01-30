from pathlib import Path

import pytest

from steinbock.segmentation import cellpose


@pytest.mark.skipif(not cellpose.cellpose_available, reason="Cellpose is not available")
class TestCellposeSegmentation:
    def test_create_segmentation_stack(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    @pytest.mark.skip(reason="Test would take too long")
    def test_try_segment_objects_nuclei(self, imc_test_data_steinbock_path: Path):
        pass  # TODO
