import numpy as np

from pathlib import Path

from steinbock import io
from steinbock.utils import matching


class TestMatchingUtils:
    def test_match_masks(self):
        mask1 = np.array(
            [
                [1, 1, 0],
                [0, 0, 0],
                [0, 2, 2],
            ],
            dtype=io.mask_dtype,
        )
        mask2 = np.array(
            [
                [3, 3, 0],
                [0, 0, 0],
                [0, 4, 4],
            ],
            dtype=io.mask_dtype,
        )
        matching.match_masks(mask1, mask2)  # TODO

    def test_try_match_masks_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        mask_files1 = io.list_mask_files(
            imc_test_data_steinbock_path / "masks"
        )
        mask_files2 = io.list_mask_files(
            imc_test_data_steinbock_path / "masks", base_files=mask_files1
        )
        gen = matching.try_match_masks_from_disk(mask_files1, mask_files2)
        for mask_file1, mask_file2, df in gen:
            pass  # TODO
