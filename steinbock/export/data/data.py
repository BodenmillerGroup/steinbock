import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Sequence, Union

from steinbock import io


def collect_data_from_disk(
    data_dirs: Sequence[Union[str, PathLike]],
) -> pd.DataFrame:
    img_file_names = []
    merged_data_objs = []
    data_file_groups = (io.list_data_files(data_dir) for data_dir in data_dirs)
    for data_files in zip(*data_file_groups):
        img_file_name = Path(data_files[0]).with_suffix(".tiff").name
        merged_data = io.read_data(data_files[0])
        for data_file in data_files[1:]:
            merged_data = pd.merge(
                merged_data,
                io.read_data(data_file),
                left_index=True,
                right_index=True,
            )
        img_file_names.append(img_file_name)
        merged_data_objs.append(merged_data)
    return pd.concat(
        merged_data_objs,
        keys=img_file_names,
        names=["Image", "Object"]
    )
