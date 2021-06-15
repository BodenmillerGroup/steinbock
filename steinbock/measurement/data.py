import numpy as np
import pandas as pd

from enum import Enum
from functools import partial
from os import PathLike
from pathlib import Path
from scipy.ndimage import measurements
from skimage.measure import regionprops_table
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


class Measurement(Enum):
    """"""

    SUM = partial(measurements.sum_labels)
    MIN = partial(measurements.minimum)
    MAX = partial(measurements.maximum)
    MEAN = partial(measurements.mean)
    MEDIAN = partial(measurements.median)
    STD = partial(measurements.standard_deviation)
    VAR = partial(measurements.variance)


def measure_intensites(
    img: np.ndarray,
    mask: np.ndarray,
    channel_names: Sequence[str],
    measurement: Measurement,
) -> pd.DataFrame:
    object_ids = np.unique(mask[mask != 0])
    data = {
        channel_name: measurement.value(img[i], labels=mask, index=object_ids)
        for i, channel_name in enumerate(channel_names)
    }
    return pd.DataFrame(
        data=data, index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
    )


def measure_intensities_from_disk(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    channel_names: Sequence[str],
    measurement: Measurement,
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        intensities = measure_intensites(
            io.read_image(img_file),
            io.read_mask(mask_file),
            channel_names,
            measurement,
        )
        yield Path(img_file), Path(mask_file), intensities
        del intensities


def measure_regionprops(
    img: np.ndarray, mask: np.ndarray, skimage_regionprops: Sequence[str]
) -> pd.DataFrame:
    data = regionprops_table(
        mask,
        intensity_image=np.moveaxis(img, 0, -1),
        properties=skimage_regionprops,
    )
    object_ids = data.pop("label")
    return pd.DataFrame(
        data=data, index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
    )


def measure_regionprops_from_disk(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    skimage_regionprops: Sequence[str],
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    skimage_regionprops = list(skimage_regionprops)
    if "label" not in skimage_regionprops:
        skimage_regionprops.insert(0, "label")
    for img_file, mask_file in zip(img_files, mask_files):
        regionprops = measure_regionprops(
            io.read_image(img_file),
            io.read_mask(mask_file),
            skimage_regionprops,
        )
        yield Path(img_file), Path(mask_file), regionprops
        del regionprops
