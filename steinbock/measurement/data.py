import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from skimage.measure import regionprops_table
from typing import Callable, Generator, Sequence, Tuple, Union

from steinbock import io


def measure_intensites(
    img: np.ndarray,
    mask: np.ndarray,
    channel_names: Sequence[str],
    aggr_func: Callable[[np.ndarray], float],
) -> pd.DataFrame:
    object_ids = np.unique(mask[mask != 0])
    data = {
        channel_name: [
            aggr_func(img[channel_index, mask == object_id])
            for object_id in object_ids
        ]
        for channel_index, channel_name in enumerate(channel_names)
    }
    return pd.DataFrame(
        data=data, index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
    )


def measure_intensities_from_disk(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    channel_names: Sequence[str],
    aggr_func: Callable[[np.ndarray], float],
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        intensities = measure_intensites(
            io.read_image(img_file),
            io.read_mask(mask_file),
            channel_names,
            aggr_func,
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
