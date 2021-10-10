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
        data.try_convert_to_dataframe_from_disk(
            intensities_files, regionprops_files
        )  # TODO

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
        gen = data.try_convert_to_anndata_from_disk(
            intensities_files, regionprops_files
        )
        for intensities_file, (regionprops_file,), anndata in gen:
            pass  # TODO
