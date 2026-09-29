from pathlib import Path

import numpy as np
import pytest

from steinbock import io
from steinbock.segmentation import cellpose


@pytest.mark.skipif(not cellpose.cellpose_available, reason="Cellpose is not available")
class TestCellposeSegmentation:
    def test_create_segmentation_stack(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    @pytest.mark.skip(reason="Test would take too long")
    def test_try_segment_objects_nuclei(self, imc_test_data_steinbock_path: Path):
        pass  # TODO


class _RescalingModel:
    def __init__(self, *args, **kwargs):
        pass

    def eval(self, imgs, **kwargs):
        img = imgs[0]
        mask = np.zeros((img.shape[1] * 2, img.shape[2] * 2), dtype=np.uint16)
        mask[4:12, 4:12] = 1
        return [mask], [None], [None]


@pytest.mark.skipif(not cellpose.cellpose_available, reason="Cellpose is not available")
def test_mask_matches_image_size(tmp_path: Path, monkeypatch):
    img_file = tmp_path / "img.tiff"
    io.write_image(np.ones((2, 30, 40), dtype=np.float32), img_file)
    monkeypatch.setattr(cellpose.models, "CellposeModel", _RescalingModel)
    results = list(cellpose.try_segment_objects([img_file], diameter=15))
    assert len(results) == 1
    mask = results[0][1]
    assert mask.shape == (30, 40)
    assert mask.dtype == np.uint16
    assert set(np.unique(mask)) == {0, 1}
