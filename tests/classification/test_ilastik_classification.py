from pathlib import Path

from steinbock.classification import ilastik


class TestIlastikClassification:
    def test_list_ilastik_image_files(
        self, imc_test_data_steinbock_path: Path
    ):
        ilastik.list_ilastik_image_files(
            imc_test_data_steinbock_path / "ilastik_img"
        )  # TODO

    def test_list_ilastik_crop_files(self, imc_test_data_steinbock_path: Path):
        ilastik.list_ilastik_crop_files(
            imc_test_data_steinbock_path / "ilastik_crops"
        )  # TODO

    def test_read_ilastik_image(self, imc_test_data_steinbock_path: Path):
        ilastik.read_ilastik_image(
            imc_test_data_steinbock_path
            / "ilastik_img"
            / "20210305_NE_mockData1_1"
        )  # TODO

    def test_read_ilastik_crop(self, imc_test_data_steinbock_path: Path):
        ilastik.read_ilastik_crop(
            imc_test_data_steinbock_path
            / "ilastik_crops"
            / "20210305_NE_mockData1_s0_a1_ac_ilastik_x0_y0_w120_h120.h5"
        )  # TODO

    def test_write_ilastik_image(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_write_ilastik_crop(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_create_ilastik_image(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_try_create_ilastik_images_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO

    def test_create_ilastik_crop(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_try_create_ilastik_crops_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO

    def test_create_and_save_ilastik_project(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO

    def test_run_pixel_classification(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO

    def test_try_fix_ilastik_crops_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO

    def test_fix_ilastik_project_file_inplace(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO
