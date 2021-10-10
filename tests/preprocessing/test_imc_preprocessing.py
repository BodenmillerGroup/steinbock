from pathlib import Path

from steinbock.preprocessing import imc


class TestIMCPreprocessing:
    def test_list_mcd_files(self, imc_test_data_steinbock_path: Path):
        imc.list_mcd_files(imc_test_data_steinbock_path / "raw")  # TODO

    def test_list_txt_files(self, imc_test_data_steinbock_path: Path):
        imc.list_txt_files(imc_test_data_steinbock_path / "raw")  # TODO

    def test_filter_hot_pixels(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_preprocess_image(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_try_preprocess_images_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO

    def test_create_panel_from_imc_panel(
        self, imc_test_data_steinbock_path: Path
    ):
        imc.create_panel_from_imc_panel(
            imc_test_data_steinbock_path / "raw" / "panel.csv"
        )  # TODO

    def test_create_panel_from_mcd_file(
        self, imc_test_data_steinbock_path: Path
    ):
        imc.create_panel_from_mcd_file(
            imc_test_data_steinbock_path
            / "raw"
            / "20210305_NE_mockData1"
            / "20210305_NE_mockData1.mcd"
        )  # TODO

    def test_create_panel_from_txt_file(
        self, imc_test_data_steinbock_path: Path
    ):
        imc.create_panel_from_txt_file(
            imc_test_data_steinbock_path
            / "raw"
            / "20210305_NE_mockData1"
            / "20210305_NE_mockData1_ROI_001_1.txt"
        )  # TODO
