from imctoolkit import SpatialCellGraph
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


def construct_knn_graphs(
    cell_data_files: Sequence[Union[str, PathLike]],
    cell_dist_files: Sequence[Union[str, PathLike]],
    num_cell_neighbors: int,
) -> Generator[Tuple[Path, Path, SpatialCellGraph], None, None]:
    it = zip(cell_data_files, cell_dist_files)
    for cell_data_file, cell_dist_file in it:
        cell_data = io.read_cell_data(cell_data_file)
        cell_dist = io.read_cell_dist(cell_dist_file)
        cell_graph = SpatialCellGraph.construct_knn_graph(
            cell_data,
            cell_dist,
            num_cell_neighbors,
        )
        yield cell_data_file, cell_dist_files, cell_graph


def construct_dist_graphs(
    cell_data_files: Sequence[Union[str, PathLike]],
    cell_dist_files: Sequence[Union[str, PathLike]],
    cell_dist_thres: float,
) -> Generator[Tuple[Path, Path, SpatialCellGraph], None, None]:
    it = zip(cell_data_files, cell_dist_files)
    for cell_data_file, cell_dist_file in it:
        cell_data = io.read_cell_data(cell_data_file)
        cell_dist = io.read_cell_dist(cell_dist_file)
        cell_graph = SpatialCellGraph.construct_dist_graph(
            cell_data,
            cell_dist,
            cell_dist_thres,
        )
        yield cell_data_file, cell_dist_files, cell_graph
