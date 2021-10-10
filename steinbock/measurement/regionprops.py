import logging
import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from skimage.measure import regionprops_table
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)


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
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for img_file, mask_file in zip(img_files, mask_files):
        try:
            regionprops = measure_regionprops(
                io.read_image(img_file),
                io.read_mask(mask_file),
                skimage_regionprops,
            )
            yield Path(img_file), Path(mask_file), regionprops
            del regionprops
        except:
            _logger.exception(f"Error measuring regionprops in {img_file}")
