import logging
import networkx as nx
import pandas as pd

from collections import Counter
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)


def convert_to_networkx(neighbors: pd.DataFrame, *data_list) -> nx.Graph:
    edges = neighbors[["Object", "Neighbor"]].astype(int).values.tolist()
    undirected_edges = [tuple(sorted(edge)) for edge in edges]
    is_directed = any([x != 2 for x in Counter(undirected_edges).values()])
    graph: nx.Graph = nx.from_pandas_edgelist(
        neighbors,
        source="Object",
        target="Neighbor",
        edge_attr=True,
        create_using=nx.DiGraph if is_directed else nx.Graph,
    )
    if len(data_list) > 0:
        merged_data = data_list[0]
        for data in data_list[1:]:
            merged_data = pd.merge(
                merged_data, data, left_index=True, right_index=True
            )
        node_attributes = {
            int(object_id): object_data.to_dict()
            for object_id, object_data in merged_data.iterrows()
        }
        nx.set_node_attributes(graph, node_attributes)
    return graph


def try_convert_to_networkx_from_disk(
    neighbors_files: Sequence[Union[str, PathLike]], *data_file_lists
) -> Generator[Tuple[Path, Tuple[Path, ...], nx.Graph], None, None]:
    for neighbors_file, *data_files in zip(neighbors_files, *data_file_lists):
        data_files = tuple(Path(data_file) for data_file in data_files)
        try:
            neighbors = io.read_neighbors(neighbors_file)
            data_list = [io.read_data(data_file) for data_file in data_files]
            graph = convert_to_networkx(neighbors, *data_list)
            yield Path(neighbors_file), data_files, graph
            del neighbors, data_list, graph
        except:
            _logger.exception(f"Error converting {neighbors_file} to networkx")
