import numpy as np

from pathlib import Path

from steinbock import io
from steinbock.measurement import intensities
from steinbock.measurement.intensities import IntensityAggregation


class TestIntensitiesMeasurement:
    def test_measure_intensites(self):
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
        channel_names = ["Channel 1", "Channel 2"]
        df = intensities.measure_intensites(
            img, mask, channel_names, IntensityAggregation.MEAN
        )
        assert np.all(df.index.values == np.array([1, 2]))
        assert np.all(df.columns.values == np.array(channel_names))
        assert np.all(df.values == np.array([[1.0, 25.0], [5.0, 150.0]]))

    def test_try_measure_intensities_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        panel = io.read_panel(imc_test_data_steinbock_path / "panel.csv")
        img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
        mask_files = io.list_mask_files(
            imc_test_data_steinbock_path / "masks", base_files=img_files
        )
        gen = intensities.try_measure_intensities_from_disk(
            img_files,
            mask_files,
            panel["name"].tolist(),
            IntensityAggregation.MEAN,
        )
        for img_file, mask_file, df in gen:
            pass  # TODO
