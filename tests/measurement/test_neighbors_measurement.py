import numpy as np

from pathlib import Path

from steinbock import io
from steinbock.measurement import neighbors
from steinbock.measurement.neighbors import NeighborhoodType


class TestNeighborsMeasurement:
    def test_measure_neighbors_centroid(self):
        mask = np.array(
            [
                [1, 1, 0],
                [3, 0, 4],
                [0, 2, 2],
            ],
            dtype=io.mask_dtype,
        )
        neighbors.measure_neighbors(
            mask,
            NeighborhoodType.CENTROID_DISTANCE,
            metric="euclidean",
            dmax=1.0,
        )  # TODO

    def test_measure_neighbors_euclidean_border(self):
        mask = np.array(
            [
                [1, 1, 0],
                [3, 0, 4],
                [0, 2, 2],
            ],
            dtype=io.mask_dtype,
        )
        neighbors.measure_neighbors(
            mask,
            NeighborhoodType.EUCLIDEAN_BORDER_DISTANCE,
            metric="euclidean",
            dmax=1.0,
        )  # TODO

    def test_measure_neighbors_euclidean_pixel_expansion(self):
        mask = np.array(
            [
                [1, 1, 0],
                [3, 0, 4],
                [0, 2, 2],
            ],
            dtype=io.mask_dtype,
        )
        neighbors.measure_neighbors(
            mask,
            NeighborhoodType.EUCLIDEAN_PIXEL_EXPANSION,
            metric="euclidean",
            dmax=1.0,
        )  # TODO

    def test_try_measure_neighbors_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        mask_files = io.list_mask_files(imc_test_data_steinbock_path / "masks")
        gen = neighbors.try_measure_neighbors_from_disk(
            mask_files,
            NeighborhoodType.CENTROID_DISTANCE,
            metric="euclidean",
            dmax=4.0,
        )
        for mask_file, df in gen:
            pass  # TODO
