import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from skimage import measure
from typing import Callable, Generator, Sequence, Tuple, Union

from steinbock.utils import io


def measure_intensities(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    channel_names: Sequence[str],
    aggr_function: Callable[[np.ndarray], float],
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        img = io.read_image(img_file)
        mask = io.read_mask(mask_file)
        object_ids = np.unique(mask[mask != 0])
        intensities_data = {
            channel_name: [
                aggr_function(img[channel_index, mask == object_id])
                for object_id in object_ids
            ]
            for channel_index, channel_name in enumerate(channel_names)
        }
        intensities = pd.DataFrame(
            data=intensities_data,
            index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
        )
        yield Path(img_file), Path(mask_file), intensities
        del intensities


def measure_regionprops(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    channel_names: Sequence[str],
    skimage_regionprops: Sequence[str],
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    skimage_regionprops = list(skimage_regionprops)
    if "label" not in skimage_regionprops:
        skimage_regionprops.insert(0, "label")
    for img_file, mask_file in zip(img_files, mask_files):
        img = io.read_image(img_file)
        mask = io.read_mask(mask_file)
        regionprops_data = measure.regionprops_table(
            mask,
            intensity_image=np.moveaxis(img, 0, -1),
            properties=skimage_regionprops,
        )
        object_ids = regionprops_data.pop("label")
        regionprops = pd.DataFrame(
            data=regionprops_data,
            index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
        )
        yield Path(img_file), Path(mask_file), regionprops
        del regionprops


def combine(data_dirs: Sequence[Union[str, PathLike]]) -> pd.DataFrame:
    objs = []
    keys = []
    data_file_groups = (io.list_data(data_dir) for data_dir in data_dirs)
    for data_files in zip(*data_file_groups):
        obj = io.read_data(data_files[0])
        for data_file in data_files[1:]:
            data = io.read_data(data_file)
            obj = pd.merge(obj, data, left_index=True, right_index=True)
        key = Path(data_files[0]).with_suffix(".tiff").name
        objs.append(obj)
        keys.append(key)
    return pd.concat(objs, keys=keys, names=["Image", "Object"])
