import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Sequence, Union

from steinbock.utils import io


def collect_data(data_dirs: Sequence[Union[str, PathLike]]) -> pd.DataFrame:
    objs = []
    keys = []
    data_file_groups = (io.list_data(data_dir) for data_dir in data_dirs)
    for data_files in zip(*data_file_groups):
        obj = io.read_data(data_files[0])
        for data_file in data_files[1:]:
            data = io.read_data(data_file)
            obj = pd.merge(obj, data, left_index=True, right_index=True)
        key = Path(data_files[0]).with_suffix(".tiff").name
        objs.append(obj)
        keys.append(key)
    return pd.concat(objs, keys=keys, names=["Image", "Object"])
