from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

import numpy as np
from skimage.segmentation import expand_labels

from .. import io


def expand_mask(mask: np.ndarray, distance: int) -> np.ndarray:
    expanded_mask = expand_labels(mask, distance=distance)
    return expanded_mask


def try_expand_masks_from_disk(
    mask_files: Sequence[Union[str, PathLike]], distance: int, mmap: bool = False
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for mask_file in mask_files:
        if mmap:
            mask = io.mmap_mask(mask_file)
        else:
            mask = io.read_mask(mask_file, native_dtype=True)
        expanded_mask = expand_mask(mask, distance=distance)
        yield Path(mask_file), expanded_mask
