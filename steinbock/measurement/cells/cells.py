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
        cell_ids = np.unique(mask[mask != 0])
        cell_intensity_data = {
            channel_name: [
                aggr_function(img[channel_index, mask == cell_id])
                for cell_id in cell_ids
            ]
            for channel_index, channel_name in enumerate(channel_names)
        }
        cell_intensities = pd.DataFrame(
            data=cell_intensity_data,
            index=pd.Index(cell_ids, dtype=np.uint16, name="Cell"),
        )
        yield Path(img_file), Path(mask_file), cell_intensities


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
        cell_regionprops_data = measure.regionprops_table(
            mask,
            intensity_image=np.moveaxis(img, 0, -1),
            properties=skimage_regionprops,
        )
        cell_ids = cell_regionprops_data.pop("label")
        cell_regionprops = pd.DataFrame(
            data=cell_regionprops_data,
            index=pd.Index(cell_ids, dtype=np.uint16, name="Cell"),
        )
        yield Path(img_file), Path(mask_file), cell_regionprops


def combine_cell_data(
    cell_data_dirs: Sequence[Union[str, PathLike]],
) -> pd.DataFrame:
    objs = []
    keys = []
    cell_data_file_groups = (
        io.list_cell_data(cell_data_dir) for cell_data_dir in cell_data_dirs
    )
    for cell_data_files in zip(*cell_data_file_groups):
        obj = io.read_cell_data(cell_data_files[0])
        for cell_data_file in cell_data_files[1:]:
            obj = pd.merge(
                obj,
                io.read_cell_data(cell_data_file),
                left_index=True,
                right_index=True,
            )
        key = Path(cell_data_files[0]).with_suffix(".tiff").name
        objs.append(obj)
        keys.append(key)
    return pd.concat(objs, keys=keys, names=["Image", "Cell"])
