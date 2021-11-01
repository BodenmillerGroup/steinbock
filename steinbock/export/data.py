import logging
import pandas as pd

from anndata import AnnData, concat as anndata_concat
from os import PathLike
from pathlib import Path
from typing import Generator, Optional, Sequence, Tuple, Union

from steinbock import io


# TODO
_logger = logging.getLogger(__name__)


def try_convert_to_dataframe_from_disk(
    *data_file_lists,
    concatenate: bool = False,
) -> Generator[
    Tuple[str, Tuple[Path, ...], pd.DataFrame], None, Optional[pd.DataFrame]
]:
    img_file_names = []
    dfs = []
    for data_files in zip(*data_file_lists):
        img_file_name = io._as_path_with_suffix(data_files[0], ".tiff").name
        data_files = tuple(Path(data_file) for data_file in data_files)
        # TODO try/catch
        df = io.read_data(data_files[0])
        for data_file in data_files[1:]:
            df = pd.merge(
                df,
                io.read_data(data_file),
                left_index=True,
                right_index=True,
            )
        yield img_file_name, data_files, df
        if concatenate:
            img_file_names.append(img_file_name)
            dfs.append(df)
        else:
            del df
    if concatenate:
        return pd.concat(dfs, keys=img_file_names, names=["Image", "Object"])


def try_convert_to_anndata_from_disk(
    x_data_files: Sequence[Union[str, PathLike]],
    *obs_data_file_lists,
    concatenate: bool = False,
) -> Generator[
    Tuple[str, Path, Tuple[Path, ...], AnnData], None, Optional[AnnData]
]:
    # TODO export image metadata
    img_file_names = []
    adatas = []
    for x_data_file, *obs_data_files in zip(
        x_data_files, *obs_data_file_lists
    ):
        img_file_name = io._as_path_with_suffix(x_data_file, ".tiff").name
        x_data_file = Path(x_data_file)
        obs_data_files = tuple(Path(obs_file) for obs_file in obs_data_files)
        # TODO try/catch
        x = io.read_data(x_data_file)
        obs = None
        if len(obs_data_files) > 0:
            obs = io.read_data(obs_data_files[0])
            for obs_file in obs_data_files[1:]:
                obs = pd.merge(
                    obs,
                    io.read_data(obs_file),
                    left_index=True,
                    right_index=True,
                )
            obs.index = obs.index.astype(str)
        adata = AnnData(X=x.values, obs=obs)
        yield img_file_name, x_data_file, obs_data_files, adata
        if concatenate:
            img_file_names.append(img_file_name)
            adatas.append(adata)
        else:
            del x, obs, adata
    if concatenate:
        return anndata_concat(adatas, keys=img_file_names, index_unique="_")
