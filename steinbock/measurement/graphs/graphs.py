import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


def construct_knn_graphs(
    cell_dists_files: Sequence[Union[str, PathLike]],
    k: int,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for cell_dists_file in cell_dists_files:
        cell_dists = io.read_cell_dists(cell_dists_file)
        cells1 = []
        cells2 = []
        for cell_id in cell_dists.index.values:
            nb_dists = cell_dists.loc[cell_id, :].values
            nb_col_indices = np.argpartition(nb_dists, k + 1)[: k + 1]
            for neighbor_cell_id in cell_dists.columns[nb_col_indices].values:
                if neighbor_cell_id != cell_id:
                    cells1.append(cell_id)
                    cells2.append(neighbor_cell_id)
        cell_graph = pd.DataFrame(
            data={
                "Cells1": np.array(cells1, dtype=np.uint16),
                "Cells2": np.array(cells2, dtype=np.uint16),
            }
        )
        yield cell_dists_file, cell_graph
        del cell_graph


def construct_dist_graphs(
    cell_dists_files: Sequence[Union[str, PathLike]],
    cell_dist_thres: float,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for cell_dists_file in cell_dists_files:
        cell_dists = io.read_cell_dists(cell_dists_file)
        indices = np.argwhere(cell_dists.values < cell_dist_thres)
        cells1 = cell_dists.index[indices[:, 0]].values.astype(np.uint16)
        cells2 = cell_dists.columns[indices[:, 1]].values.astype(np.uint16)
        cell_graph = pd.DataFrame(data={"Cells1": cells1, "Cells2": cells2})
        yield cell_dists_file, cell_graph
        del cell_graph
