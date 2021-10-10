import pandas as pd

from pathlib import Path

from steinbock import io
from steinbock.export import graphs


class TestGraphsExport:
    def test_convert_to_networkx(self):
        neighbors = pd.DataFrame(
            data={
                "Object": [1, 2],
                "Neighbor": [2, 1],
                "Distance": [1.0, 1.0],
            }
        )
        neighbors["Object"] = neighbors["Object"].astype(io.mask_dtype)
        neighbors["Neighbor"] = neighbors["Neighbor"].astype(io.mask_dtype)
        intensities = pd.DataFrame(
            data={
                "Channel 1": [1.0, 2.0],
                "Channel 2": [100.0, 200.0],
            },
            index=pd.Index([1, 2], name="Object", dtype=io.mask_dtype),
        )
        graphs.convert_to_networkx(neighbors, intensities)  # TODO

    def test_try_convert_to_networkx_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        neighbors_files = io.list_neighbors_files(
            imc_test_data_steinbock_path / "neighbors"
        )
        intensities_files = io.list_data_files(
            imc_test_data_steinbock_path / "intensities",
            base_files=neighbors_files,
        )
        gen = graphs.try_convert_to_networkx_from_disk(
            neighbors_files, intensities_files
        )
        for neighbors_file, (intensities_file,), graph in gen:
            pass  # TODO
