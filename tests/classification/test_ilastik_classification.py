import numpy as np
import pytest
import shutil

from pathlib import Path

from steinbock import io
from steinbock._env import ilastik_binary
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

    def test_write_ilastik_image(self, tmp_path: Path):
        ilastik_img = np.array(
            [
                [
                    [1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9],
                ]
            ],
            dtype=io.img_dtype,
        )
        ilastik.write_ilastik_image(
            ilastik_img, tmp_path / "ilastik_img"
        )  # TODO

    def test_write_ilastik_crop(self, tmp_path: Path):
        ilastik_crop = np.array(
            [
                [
                    [1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9],
                ]
            ],
            dtype=io.img_dtype,
        )
        ilastik.write_ilastik_crop(
            ilastik_crop, tmp_path / "ilastik_crop"
        )  # TODO

    def test_create_ilastik_image(self):
        img = np.array(
            [
                [
                    [1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9],
                ]
            ],
            dtype=io.img_dtype,
        )
        ilastik_img = ilastik.create_ilastik_image(img)
        expected_ilastik_img = np.array(
            [
                [
                    [100, 200, 300],
                    [400, 500, 600],
                    [700, 800, 900],
                ],
                [
                    [1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9],
                ],
            ],
            dtype=io.img_dtype,
        )
        assert np.all(ilastik_img == expected_ilastik_img)

    def test_try_create_ilastik_images_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
        gen = ilastik.try_create_ilastik_images_from_disk(img_files)
        for img_file, ilastik_img in gen:
            pass  # TODO

    def test_create_ilastik_crop(self):
        ilastik_img = np.array(
            [
                [
                    [100, 200, 300],
                    [400, 500, 600],
                    [700, 800, 900],
                ],
                [
                    [1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9],
                ],
            ],
            dtype=io.img_dtype,
        )
        rng = np.random.default_rng()
        x, y, ilastik_crop = ilastik.create_ilastik_crop(ilastik_img, 3, rng)
        expected_ilastik_crop = np.array(
            [
                [
                    [100, 200, 300],
                    [400, 500, 600],
                    [700, 800, 900],
                ],
                [
                    [1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9],
                ],
            ],
            dtype=io.img_dtype,
        )
        assert np.all(ilastik_crop == expected_ilastik_crop)

    def test_try_create_ilastik_crops_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        ilastik_img_files = ilastik.list_ilastik_image_files(
            imc_test_data_steinbock_path / "ilastik_img"
        )
        rng = np.random.default_rng(seed=123)
        gen = ilastik.try_create_ilastik_crops_from_disk(
            ilastik_img_files, 50, rng
        )
        for ilastik_img_file, x, y, ilastik_crop in gen:
            pass  # TODO

    def test_create_and_save_ilastik_project(
        self, imc_test_data_steinbock_path: Path, tmp_path: Path
    ):
        shutil.copytree(
            imc_test_data_steinbock_path / "ilastik_crops",
            tmp_path / "ilastik_crops",
        )
        ilastik_crop_files = ilastik.list_ilastik_crop_files(
            tmp_path / "ilastik_crops"
        )
        ilastik.create_and_save_ilastik_project(
            ilastik_crop_files, tmp_path / "pixel_classifier.ilp"
        )  # TODO

    @pytest.mark.skip(reason="Test would take too long")
    @pytest.mark.skipif(
        shutil.which(ilastik_binary) is None, reason="Ilastik is not available"
    )
    def test_run_pixel_classification(
        self, imc_test_data_steinbock_path: Path, tmp_path: Path
    ):
        shutil.copytree(
            imc_test_data_steinbock_path / "ilastik_img",
            tmp_path / "ilastik_img",
        )
        ilastik_img_files = ilastik.list_ilastik_image_files(
            tmp_path / "ilastik_img"
        )
        ilastik.run_pixel_classification(
            ilastik_binary,
            imc_test_data_steinbock_path / "pixel_classifier.ilp",
            ilastik_img_files,
            tmp_path / "ilastik_probabilities",
        )  # TODO

    def test_try_fix_ilastik_crops_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO

    def test_fix_ilastik_project_file_inplace(
        self, imc_test_data_steinbock_path: Path
    ):
        pass  # TODO
