import networkx as nx
import pandas as pd

from collections import Counter
from os import PathLike
from pathlib import Path
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


def to_networkx(graph: pd.DataFrame, *data_list) -> nx.Graph:
    edges = graph[["Object1", "Object2"]].astype(int).values.tolist()
    undirected_edges = [tuple(sorted(edge)) for edge in edges]
    is_directed = any([x != 2 for x in Counter(undirected_edges).values()])
    g: nx.Graph = nx.from_pandas_edgelist(
        graph,
        source="Object1",
        target="Object2",
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
        nx.set_node_attributes(g, node_attributes)
    return g


def to_networkx_from_disk(
    graph_files: Sequence[Union[str, PathLike]], *data_file_lists
) -> Generator[Tuple[Path, nx.Graph], None, None]:
    for i, graph_file in enumerate(graph_files):
        graph = io.read_graph(graph_file)
        data_list = []
        for data_files in data_file_lists:
            data_list.append(io.read_data(data_files[i]))
        g = to_networkx(graph, *data_list)
        yield Path(graph_file), g
        del graph, data_list, g
