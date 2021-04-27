import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
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
        data = {
            channel_name: [
                aggr_function(img[channel_index, mask == object_id])
                for object_id in object_ids
            ]
            for channel_index, channel_name in enumerate(channel_names)
        }
        df = pd.DataFrame(
            data=data,
            index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
        )
        yield Path(img_file), Path(mask_file), df
        del df
