import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


def construct_knn_graphs(
    distances_files: Sequence[Union[str, PathLike]],
    k: int,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for distances_file in distances_files:
        d = io.read_distances(distances_file)
        source_object_ids = []
        target_object_ids = []
        for object_id in d.index.values:
            d_neighbors = d.loc[object_id, :].values
            neighbor_col_ind = np.argpartition(d_neighbors, k + 1)[: k + 1]
            neighbor_object_ids = d.columns[neighbor_col_ind].values
            for neighbor_object_id in neighbor_object_ids:
                if neighbor_object_id != object_id:
                    source_object_ids.append(object_id)
                    target_object_ids.append(neighbor_object_id)
        g = pd.DataFrame(
            data={
                "Object1": np.array(source_object_ids, dtype=np.uint16),
                "Object2": np.array(target_object_ids, dtype=np.uint16),
            }
        )
        yield distances_file, g
        del g


def construct_distance_graphs(
    distances_files: Sequence[Union[str, PathLike]],
    distance_threshold: float,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for distances_file in distances_files:
        d = io.read_distances(distances_file)
        indices = np.argwhere(d.values < distance_threshold)
        source_object_ids = d.index[indices[:, 0]].values
        target_object_ids = d.columns[indices[:, 1]].values
        g = pd.DataFrame(
            data={
                "Object1": source_object_ids.astype(np.uint16),
                "Object2": target_object_ids.astype(np.uint16),
            }
        )
        yield distances_file, g
        del g
