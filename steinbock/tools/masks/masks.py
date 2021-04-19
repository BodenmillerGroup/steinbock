import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


def match(
    mask_files1: Sequence[Union[str, PathLike]],
    mask_files2: Sequence[Union[str, PathLike]],
) -> Generator[Tuple[Path, Path, pd.DataFrame], None, None]:
    for mask_file1, mask_file2 in zip(mask_files1, mask_files2):
        mask1 = io.read_mask(mask_file1)
        mask2 = io.read_mask(mask_file2)
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
        table = pd.DataFrame(
            data={
                "Object1": object_ids1,
                "Object2": object_ids2,
            }
        )
        table.drop_duplicates(inplace=True, ignore_index=True)
        yield mask_file1, mask_file2, table
        del table
