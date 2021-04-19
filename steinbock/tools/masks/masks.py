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
        nonzero1 = mask1 != 0
        nonzero2 = mask2 != 0
        cell_ids1 = []
        cell_ids2 = []
        for cell_id1 in np.unique(mask1[nonzero1]):
            for cell_id2 in np.unique(mask2[nonzero2 & (mask1 == cell_id1)]):
                cell_ids1.append(cell_id1)
                cell_ids2.append(cell_id2)
        for cell_id2 in np.unique(mask2[nonzero2]):
            for cell_id1 in np.unique(mask1[nonzero1 & (mask2 == cell_id2)]):
                cell_ids1.append(cell_id1)
                cell_ids2.append(cell_id2)
        table = pd.DataFrame(data={"First": cell_ids1, "Second": cell_ids2})
        table.drop_duplicates(inplace=True, ignore_index=True)
        yield mask_file1, mask_file2, table
        del table
