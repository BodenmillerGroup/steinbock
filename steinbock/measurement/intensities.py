import logging
from enum import Enum
from functools import partial
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

import numpy as np
import pandas as pd
import scipy.ndimage

from .. import io

logger = logging.getLogger(__name__)


class IntensityAggregation(Enum):
    SUM = partial(scipy.ndimage.sum_labels)
    MIN = partial(scipy.ndimage.minimum)
    MAX = partial(scipy.ndimage.maximum)
    MEAN = partial(scipy.ndimage.mean)
    MEDIAN = partial(scipy.ndimage.median)
    STD = partial(scipy.ndimage.standard_deviation)
    VAR = partial(scipy.ndimage.variance)


def measure_intensites(
    img: np.ndarray,
    mask: np.ndarray,
    channel_names: Sequence[str],
    intensity_aggregation: IntensityAggregation,
) -> pd.DataFrame:
    object_ids = np.unique(mask[mask != 0])
    data = {
        channel_name: intensity_aggregation.value(img[i], labels=mask, index=object_ids)
        for i, channel_name in enumerate(channel_names)
    }
    return pd.DataFrame(
        data=data,
        index=pd.Index(object_ids, dtype=io.mask_dtype, name="Object"),
    )


def try_measure_intensities_from_disk(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    channel_names: Sequence[str],
    intensity_aggregation: IntensityAggregation,
    mmap: bool = False,
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        try:
            if mmap:
                img = io.mmap_image(img_file)
                mask = io.mmap_mask(mask_file)
            else:
                img = io.read_image(img_file)
                mask = io.read_mask(mask_file)
            intensities = measure_intensites(
                img, mask, channel_names, intensity_aggregation
            )
            del img, mask
            yield Path(img_file), Path(mask_file), intensities
            del intensities
        except Exception as e:
            logger.exception(f"Error measuring intensities in {img_file}: {e}")
