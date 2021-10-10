import logging
import pandas as pd

from anndata import AnnData
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)


def try_convert_to_dataframe_from_disk(*data_file_lists) -> pd.DataFrame:
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
        img_file = io._as_path_with_suffix(data_files[0], ".tiff")
        data_objs.append(data)
        img_file_names.append(img_file.name)
    return pd.concat(data_objs, keys=img_file_names, names=["Image", "Object"])


def try_convert_to_anndata_from_disk(
    x_files: Sequence[Union[str, PathLike]], *obs_file_lists
) -> Generator[Tuple[Path, Tuple[Path, ...], AnnData], None, None]:
    for x_file, *obs_files in zip(x_files, *obs_file_lists):
        obs_files = tuple(Path(obs_file) for obs_file in obs_files)
        try:
            x = io.read_data(x_file)
            obs = None
            if len(obs_files) > 0:
                obs = io.read_data(obs_files[0])
                for obs_file in obs_files[1:]:
                    obs = pd.merge(
                        obs,
                        io.read_data(obs_file),
                        left_index=True,
                        right_index=True,
                    )
                obs.index = obs.index.astype(str)
            anndata = AnnData(X=x.values, obs=obs)
            yield Path(x_file), obs_files, anndata
            del x, obs
        except:
            _logger.exception(f"Error converting {x_file} to AnnData")
