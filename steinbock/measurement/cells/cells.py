import pandas as pd

from imctoolkit import ImageSingleCellData
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


def measure_cell_intensities(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    channel_names: Sequence[str],
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        img_file = Path(img_file)
        mask_file = Path(mask_file)
        img = io.read_image(img_file)
        mask = io.read_mask(mask_file)
        data = ImageSingleCellData(img, mask, channel_names=channel_names)
        yield img_file, mask_file, data.mean_intensities_table


def combine_cell_data(
    cell_data_files: Sequence[Union[str, PathLike]],
) -> pd.DataFrame:
    objs = [io.read_cell_data(f) for f in cell_data_files]
    keys = [Path(f).with_suffix(".tiff").name for f in cell_data_files]
    return pd.concat(objs, keys=keys, names=["image", "cell"])
