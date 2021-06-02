import pandas as pd

from anndata import AnnData
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


def to_table_from_disk(*data_file_lists) -> pd.DataFrame:
    data_objs = []
    img_file_names = []
    for data_files in zip(*data_file_lists):
        data = io.read_data(data_files[0])
        for data_file in data_files[1:]:
            data = pd.merge(
                data,
                io.read_data(data_file),
                left_index=True,
                right_index=True,
            )
        data_objs.append(data)
        img_file_names.append(Path(data_files[0]).with_suffix(".tiff").name)
    return pd.concat(data_objs, keys=img_file_names, names=["Image", "Object"])


def to_anndata_from_disk(
    x_files: Sequence[Union[str, PathLike]], *obs_file_lists
) -> Generator[Tuple[Path, AnnData], None, None]:
    for i, x_file in enumerate(x_files):
        x = io.read_data(x_file)
        obs = None
        if len(obs_file_lists) > 0:
            obs = io.read_data(obs_file_lists[0][i])
            for arg in obs_file_lists[1:]:
                obs = pd.merge(
                    obs,
                    io.read_data(arg[i]),
                    left_index=True,
                    right_index=True,
                )
        yield Path(x_file), AnnData(X=x, obs=obs)
        del x, obs