import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Callable, Generator, Sequence, Tuple, Union

from steinbock import io


def measure_intensites(
    img: np.ndarray,
    mask: np.ndarray,
    channel_names: Sequence[str],
    aggr: Callable[[np.ndarray], float],
) -> pd.DataFrame:
    object_ids = np.unique(mask[mask != 0])
    intensities_data = {
        channel_name: [
            aggr(img[channel_index, mask == object_id])
            for object_id in object_ids
        ]
        for channel_index, channel_name in enumerate(channel_names)
    }
    return pd.DataFrame(
        data=intensities_data,
        index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
    )


def measure_intensities_from_disk(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    channel_names: Sequence[str],
    aggr_function: Callable[[np.ndarray], float],
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        img = io.read_image(img_file)
        mask = io.read_mask(mask_file)
        intensities = measure_intensites(
            img,
            mask,
            channel_names,
            aggr_function,
        )
        del img, mask
        yield Path(img_file), Path(mask_file), intensities
        del intensities
