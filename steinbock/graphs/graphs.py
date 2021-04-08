import xarray as xr

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
        cell_dist_array = xr.DataArray(
            io.read_cell_dist(cell_dist_file),
            dims=("cell_i", "cell_j"),
            coords={
                "cell_i": cell_data.index.values,
                "cell_j": cell_data.index.values,
            },
        )
        graph = SpatialCellGraph.construct_knn_graph(
            cell_data,
            cell_dist_array,
            num_cell_neighbors,
        )
        yield cell_data_file, cell_dist_files, graph


def construct_dist_graphs(
    cell_data_files: Sequence[Union[str, PathLike]],
    cell_dist_files: Sequence[Union[str, PathLike]],
    cell_dist_thres: float,
) -> Generator[Tuple[Path, Path, SpatialCellGraph], None, None]:
    it = zip(cell_data_files, cell_dist_files)
    for cell_data_file, cell_dist_file in it:
        cell_data = io.read_cell_data(cell_data_file)
        cell_dist_array = xr.DataArray(
            io.read_cell_dist(cell_dist_file),
            dims=("cell_i", "cell_j"),
            coords={
                "cell_i": cell_data.index.values,
                "cell_j": cell_data.index.values,
            },
        )
        graph = SpatialCellGraph.construct_dist_graph(
            cell_data,
            cell_dist_array,
            cell_dist_thres,
        )
        yield cell_data_file, cell_dist_files, graph
