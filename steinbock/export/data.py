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
        img_file = io.as_path_with_suffix(data_files[0], ".tiff")
        data_objs.append(data)
        img_file_names.append(img_file.name)
    return pd.concat(data_objs, keys=img_file_names, names=["Image", "Object"])


def try_convert_to_anndata_from_disk(
    x_files: Sequence[Union[str, PathLike]], *obs_file_lists
) -> Generator[Tuple[Path, AnnData], None, None]:
    for i, x_file in enumerate(x_files):
        try:
            x = io.read_data(x_file)
            merged_obs = None
            if len(obs_file_lists) > 0:
                merged_obs = io.read_data(obs_file_lists[0][i])
                for obs_files in obs_file_lists[1:]:
                    merged_obs = pd.merge(
                        merged_obs,
                        io.read_data(obs_files[i]),
                        left_index=True,
                        right_index=True,
                    )
                merged_obs.index = merged_obs.index.astype(str)
            yield Path(x_file), AnnData(X=x.values, obs=merged_obs)
            del x, merged_obs
        except:
            _logger.exception(f"Error converting {x_file} to AnnData")
