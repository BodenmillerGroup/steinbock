import logging
import numpy as np
import pandas as pd

from enum import Enum
from functools import partial
from os import PathLike
from pathlib import Path
from scipy.ndimage import measurements
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)


class IntensityAggregation(Enum):
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
    intensity_aggregation: IntensityAggregation,
) -> pd.DataFrame:
    object_ids = np.unique(mask[mask != 0])
    data = {
        channel_name: intensity_aggregation.value(
            img[i], labels=mask, index=object_ids
        )
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
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        try:
            intensities = measure_intensites(
                io.read_image(img_file),
                io.read_mask(mask_file),
                channel_names,
                intensity_aggregation,
            )
            yield Path(img_file), Path(mask_file), intensities
            del intensities
        except:
            _logger.exception(f"Error measuring intensities in {img_file}")
