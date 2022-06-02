import logging
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from skimage.measure import regionprops_table

from .. import io

logger = logging.getLogger(__name__)


def measure_regionprops(
    img: np.ndarray, mask: np.ndarray, skimage_regionprops: Sequence[str]
) -> pd.DataFrame:
    skimage_regionprops = list(skimage_regionprops)
    if "label" not in skimage_regionprops:
        skimage_regionprops.insert(0, "label")
    data = regionprops_table(
        mask,
        intensity_image=np.moveaxis(img, 0, -1),
        properties=skimage_regionprops,
    )
    object_ids = data.pop("label")
    return pd.DataFrame(
        data=data,
        index=pd.Index(object_ids, dtype=io.mask_dtype, name="Object"),
    )


def try_measure_regionprops_from_disk(
    img_files: Sequence[Union[str, PathLike]],
    mask_files: Sequence[Union[str, PathLike]],
    skimage_regionprops: Sequence[str],
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
            regionprops = measure_regionprops(img, mask, skimage_regionprops)
            del img, mask
            yield Path(img_file), Path(mask_file), regionprops
            del regionprops
        except:
            logger.exception(f"Error measuring regionprops in {img_file}")
