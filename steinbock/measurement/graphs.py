import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Generator, Optional, Sequence, Tuple, Union

from steinbock import io


def construct_graph(
    dists: pd.DataFrame,
    dmax: Optional[float] = None,
    kmax: Optional[float] = None,
) -> pd.DataFrame:
    source_object_ids = []
    target_object_ids = []
    for i, source_object_id in enumerate(dists.index.values):
        neighbor_dists = dists.loc[source_object_id, :].values
        neighbor_mask = np.ones(len(dists.columns), dtype=bool)
        neighbor_mask[i] = False
        if dmax is not None:
            neighbor_mask &= neighbor_dists <= dmax
        n = np.count_nonzero(neighbor_mask)
        if kmax is not None and n > 0:
            k = min(kmax, n)
            p = np.argpartition(neighbor_dists[neighbor_mask], k - 1)[:k]
            neighbor_indices = np.flatnonzero(neighbor_mask)[p]
            neighbor_mask = np.zeros_like(neighbor_mask)
            neighbor_mask[neighbor_indices] = True
        for target_object_id in dists.columns.values[neighbor_mask]:
            source_object_ids.append(source_object_id)
            target_object_ids.append(target_object_id)
    return pd.DataFrame(
        data={
            "Object1": np.asarray(source_object_ids, dtype=np.uint16),
            "Object2": np.asarray(target_object_ids, dtype=np.uint16),
        }
    )


def construct_graphs_from_disk(
    dists_files: Sequence[Union[str, PathLike]],
    dmax: Optional[float] = None,
    kmax: Optional[float] = None,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for dists_file in dists_files:
        graph = construct_graph(
            io.read_distances(dists_file), dmax=dmax, kmax=kmax
        )
        yield Path(dists_file), graph
        del graph
