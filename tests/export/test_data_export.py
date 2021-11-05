from pathlib import Path

from steinbock import io
from steinbock.export import data


class TestDataExport:
    def test_try_convert_to_dataframe_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        intensities_files = io.list_data_files(
            imc_test_data_steinbock_path / "intensities"
        )
        regionprops_files = io.list_data_files(
            imc_test_data_steinbock_path / "regionprops",
            base_files=intensities_files,
        )
        gen = data.try_convert_to_dataframe_from_disk(
            intensities_files, regionprops_files
        )
        for img_file_name, data_files, df in gen:
            pass  # TODO

    def test_try_convert_to_anndata_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        intensities_files = io.list_data_files(
            imc_test_data_steinbock_path / "intensities"
        )
        regionprops_files = io.list_data_files(
            imc_test_data_steinbock_path / "regionprops",
            base_files=intensities_files,
        )
        neighbors_files = io.list_neighbors_files(
            imc_test_data_steinbock_path / "neighbors",
            base_files=intensities_files,
        )
        gen = data.try_convert_to_anndata_from_disk(
            intensities_files,
            regionprops_files,
            neighbors_files=neighbors_files,
        )
        for (
            img_file_name,
            intensities_file,
            (regionprops_file, ),
            neighbors_file,
            adata,
        ) in gen:
            pass  # TODO
