import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from skimage.measure import regionprops_table
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


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
        data = regionprops_table(
            mask,
            intensity_image=np.moveaxis(img, 0, -1),
            properties=skimage_regionprops,
        )
        object_ids = data.pop("label")
        df = pd.DataFrame(
            data=data,
            index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
        )
        yield Path(img_file), Path(mask_file), df
        del df
