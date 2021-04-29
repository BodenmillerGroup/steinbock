import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


def construct_knn_graphs(
    dists_files: Sequence[Union[str, PathLike]],
    k: int,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for dists_file in dists_files:
        df = io.read_distances(dists_file)
        source_object_ids = []
        target_object_ids = []
        for object_id in df.index.values:
            d_neighbors = df.loc[object_id, :].values
            neighbor_col_ind = np.argpartition(d_neighbors, k + 1)[: k + 1]
            neighbor_object_ids = df.columns[neighbor_col_ind].values
            for neighbor_object_id in neighbor_object_ids:
                if neighbor_object_id != object_id:
                    source_object_ids.append(object_id)
                    target_object_ids.append(neighbor_object_id)
        df = pd.DataFrame(
            data={
                "Object1": np.array(source_object_ids, dtype=np.uint16),
                "Object2": np.array(target_object_ids, dtype=np.uint16),
            }
        )
        yield dists_file, df
        del df


def construct_distance_graphs(
    dists_files: Sequence[Union[str, PathLike]],
    dist_thres: float,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for dists_file in dists_files:
        df = io.read_distances(dists_file)
        indices = np.argwhere(df.values < dist_thres)
        source_object_ids = df.index[indices[:, 0]].values
        target_object_ids = df.columns[indices[:, 1]].values
        df = pd.DataFrame(
            data={
                "Object1": source_object_ids.astype(np.uint16),
                "Object2": target_object_ids.astype(np.uint16),
            }
        )
        yield dists_file, df
        del df
