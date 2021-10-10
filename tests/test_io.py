from pathlib import Path

from steinbock import io


class TestIO:
    def test_read_panel(self, imc_test_data_steinbock_path: Path):
        io.read_panel(imc_test_data_steinbock_path / "panel.csv")  # TODO

    def test_write_panel(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_list_image_files(self, imc_test_data_steinbock_path: Path):
        io.list_image_files(imc_test_data_steinbock_path / "img")  # TODO

    def test_read_image(self, imc_test_data_steinbock_path: Path):
        io.read_image(
            imc_test_data_steinbock_path / "img" / "20210305_NE_mockData1_1"
        )  # TODO

    def test_write_image(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_read_image_info(self, imc_test_data_steinbock_path: Path):
        io.read_image_info(imc_test_data_steinbock_path / "images.csv")  # TODO

    def test_write_image_info(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_list_mask_files(self, imc_test_data_steinbock_path: Path):
        io.list_mask_files(imc_test_data_steinbock_path / "masks")  # TODO

    def test_read_mask(self, imc_test_data_steinbock_path: Path):
        io.read_mask(
            imc_test_data_steinbock_path / "masks" / "20210305_NE_mockData1_1"
        )  # TODO

    def test_write_mask(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_list_data_files(self, imc_test_data_steinbock_path: Path):
        io.list_data_files(
            imc_test_data_steinbock_path / "intensities"
        )  # TODO

    def test_read_data(self, imc_test_data_steinbock_path: Path):
        io.read_data(
            imc_test_data_steinbock_path
            / "intensities"
            / "20210305_NE_mockData1_1"
        )  # TODO

    def test_write_data(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_list_neighbors_files(self, imc_test_data_steinbock_path: Path):
        io.list_neighbors_files(
            imc_test_data_steinbock_path
            / "neighbors"
            / "20210305_NE_mockData1_1"
        )  # TODO

    def test_read_neighbors(self, imc_test_data_steinbock_path: Path):
        io.read_neighbors(
            imc_test_data_steinbock_path
            / "neighbors"
            / "20210305_NE_mockData1_1"
        )  # TODO

    def test_write_neighbors(self, imc_test_data_steinbock_path: Path):
        pass  # TODO
