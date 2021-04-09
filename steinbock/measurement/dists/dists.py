import numpy as np

from imctoolkit import ImageSingleCellData
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


def measure_cell_centroid_dists(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    metric: str,
) -> Generator[Tuple[Path, Path, np.ndarray], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        img_file = Path(img_file)
        mask_file = Path(mask_file)
        img = io.read_image(img_file)
        mask = io.read_mask(mask_file)
        data = ImageSingleCellData(img, mask)
        cell_dists = data.compute_cell_centroid_distances(metric=metric).values
        yield img_file, mask_file, cell_dists


def measure_euclidean_cell_border_dists(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
) -> Generator[Tuple[Path, Path, np.ndarray], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        img_file = Path(img_file)
        mask_file = Path(mask_file)
        img = io.read_image(img_file)
        mask = io.read_mask(mask_file)
        data = ImageSingleCellData(img, mask)
        cell_dists = data.compute_cell_border_distances().values
        yield img_file, mask_file, cell_dists
