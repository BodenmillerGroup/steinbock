import logging
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from .. import io

logger = logging.getLogger(__name__)


def match_masks(mask1: np.ndarray, mask2: np.ndarray) -> pd.DataFrame:
    nz1 = mask1 != 0
    nz2 = mask2 != 0
    object_ids1 = []
    object_ids2 = []
    for object_id1 in np.unique(mask1[nz1]):
        for object_id2 in np.unique(mask2[nz2 & (mask1 == object_id1)]):
            object_ids1.append(object_id1)
            object_ids2.append(object_id2)
    for object_id2 in np.unique(mask2[nz2]):
        for object_id1 in np.unique(mask1[nz1 & (mask2 == object_id2)]):
            object_ids1.append(object_id1)
            object_ids2.append(object_id2)
    df = pd.DataFrame(data={"Object1": object_ids1, "Object2": object_ids2})
    df.drop_duplicates(inplace=True, ignore_index=True)
    return df


def try_match_masks_from_disk(
    mask_files1: Sequence[Union[str, PathLike]],
    mask_files2: Sequence[Union[str, PathLike]],
    mmap: bool = False,
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for mask_file1, mask_file2 in zip(mask_files1, mask_files2):
        try:
            if mmap:
                mask1 = io.mmap_mask(mask_file1)
                mask2 = io.mmap_mask(mask_file2)
            else:
                mask1 = io.read_mask(mask_file1)
                mask2 = io.read_mask(mask_file2)
            df = match_masks(mask1, mask2)
            del mask1, mask2
            yield mask_file1, mask_file2, df
            del df
        except:
            logger.exception(f"Error matching masks {mask_file1, mask_file2}")
