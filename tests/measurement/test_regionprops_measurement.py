import numpy as np

from pathlib import Path

from steinbock import io
from steinbock.measurement import regionprops


class TestRegionpropsMeasurement:
    def test_measure_regionprops(self):
        img = np.array(
            [
                [
                    [0.5, 1.5, 0.1],
                    [0.1, 0.2, 0.3],
                    [0.1, 6.5, 3.5],
                ],
                [
                    [20, 30, 1],
                    [1, 2, 3],
                    [1, 100, 200],
                ],
            ],
            dtype=io.img_dtype,
        )
        mask = np.array(
            [
                [1, 1, 0],
                [0, 0, 0],
                [0, 2, 2],
            ],
            dtype=io.mask_dtype,
        )
        regionprops.measure_regionprops(img, mask, ["area"])  # TODO

    def test_try_measure_regionprops_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
        mask_files = io.list_mask_files(
            imc_test_data_steinbock_path / "masks", base_files=img_files
        )
        gen = regionprops.try_measure_regionprops_from_disk(
            img_files, mask_files, ["area"]
        )
        for img_file, mask_file, df in gen:
            pass  # TODO
