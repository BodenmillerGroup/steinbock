import logging
import numpy as np
import pandas as pd

from anndata import AnnData
from os import PathLike
from pathlib import Path
from scipy.sparse import csr_matrix
from typing import Generator, Optional, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)


def try_convert_to_dataframe_from_disk(
    *data_file_lists,
) -> Generator[Tuple[str, Tuple[Path, ...], pd.DataFrame], None, None]:
    for data_files in zip(*data_file_lists):
        data_files = tuple(Path(data_file) for data_file in data_files)
        img_file_name = io._as_path_with_suffix(data_files[0], ".tiff").name
        try:
            df = io.read_data(data_files[0])
            for data_file in data_files[1:]:
                df = pd.merge(
                    df,
                    io.read_data(data_file),
                    left_index=True,
                    right_index=True,
                )
            yield img_file_name, data_files, df
            del df
        except:
            _logger.exception(
                f"Error creating DataFrame for image {img_file_name}; "
                "skipping image"
            )


def try_convert_to_anndata_from_disk(
    intensity_files: Sequence[Union[str, PathLike]],
    *data_file_lists,
    neighbors_files: Optional[Sequence[Union[str, PathLike]]] = None,
    # panel: Optional[pd.DataFrame] = None,
    # image_info: Optional[pd.DataFrame] = None,
) -> Generator[
    Tuple[str, Path, Tuple[Path, ...], Optional[Path], AnnData], None, None
]:
    # if panel is not None:
    #     panel = panel.set_index("name", drop=False, verify_integrity=True)
    # if image_info is not None:
    #     image_info = image_info.set_index(
    #         "image", drop=False, verify_integrity=True
    #     )
    for i, intensity_file in enumerate(intensity_files):
        intensity_file = Path(intensity_file)
        data_files = tuple(Path(dfl[i]) for dfl in data_file_lists)
        neighbors_file = None
        if neighbors_files is not None:
            neighbors_file = Path(neighbors_files[i])
        img_file_name = io._as_path_with_suffix(intensity_file, ".tiff").name
        try:
            x = io.read_data(intensity_file)
            obs = None
            if len(data_files) > 0:
                obs = io.read_data(data_files[0])
                for data_file in data_files[1:]:
                    obs = pd.merge(
                        obs,
                        io.read_data(data_file),
                        left_index=True,
                        right_index=True,
                    )
                obs = obs.loc[x.index, :]
            # if image_info is not None:
            #     image_obs = (
            #         pd.concat(
            #             [image_info.loc[img_file_name, :]] * len(x.index),
            #             axis=1,
            #         )
            #         .transpose()
            #         .astype(image_info.dtypes.to_dict())
            #     )
            #     image_obs.index = x.index
            #     image_obs.columns = "image_" + image_obs.columns
            #     image_obs.rename(
            #         columns={"image_image": "image"}, inplace=True
            #     )
            #     if obs is not None:
            #         obs = pd.merge(
            #             obs,
            #             image_obs,
            #             how="inner",  # preserves order of left keys
            #             left_index=True,
            #             right_index=True,
            #         )
            #     else:
            #         obs = image_obs
            var = None
            # if panel is not None:
            #     var = panel.loc[x.columns, :].copy()
            if obs is not None:
                obs.index = [f"Object {object_id}" for object_id in x.index]
            if var is not None:
                var.index = x.columns.astype(str).tolist()
            adata = AnnData(X=x.values, obs=obs, var=var)
            if neighbors_file is not None:
                neighbors = io.read_neighbors(neighbors_file)
                row_ind = [x.index.get_loc(a) for a in neighbors["Object"]]
                col_ind = [x.index.get_loc(b) for b in neighbors["Neighbor"]]
                adata.obsp["adj"] = csr_matrix(
                    ([True] * len(neighbors.index), (row_ind, col_ind)),
                    shape=(adata.n_obs, adata.n_obs),
                    dtype=np.uint8,
                )
                if neighbors["Distance"].notna().any():
                    adata.obsp["dist"] = csr_matrix(
                        (neighbors["Distance"].values, (row_ind, col_ind)),
                        shape=(adata.n_obs, adata.n_obs),
                        dtype=np.float32,
                    )
                del neighbors
            yield (
                img_file_name,
                intensity_file,
                data_files,
                neighbors_file,
                adata,
            )
            del x, obs, var, adata
        except:
            _logger.exception(
                f"Error creating AnnData object for image {img_file_name}; "
                "skipping image"
            )
