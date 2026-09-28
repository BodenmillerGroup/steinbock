import shutil
from pathlib import Path

import numpy as np
import pytest
from click.testing import CliRunner

from steinbock import io
from steinbock._cli import steinbock_cmd_group
from steinbock.preprocessing import imc


@pytest.mark.skipif(not imc.imc_available, reason="IMC is not available")
class TestIMCPreprocessing:
    def test_list_mcd_files(self, imc_test_data_steinbock_path: Path):
        imc.list_mcd_files(imc_test_data_steinbock_path / "raw")  # TODO

    def test_list_txt_files(self, imc_test_data_steinbock_path: Path):
        imc.list_txt_files(imc_test_data_steinbock_path / "raw")  # TODO

    def test_create_panel_from_imc_panel(self, imc_test_data_steinbock_path: Path):
        imc.create_panel_from_imc_panel(
            imc_test_data_steinbock_path / "raw" / "panel.csv"
        )  # TODO

    def test_create_panel_from_mcd_file(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_create_panel_from_mcd_files(self, imc_test_data_steinbock_path: Path):
        mcd_files = imc.list_mcd_files(
            imc_test_data_steinbock_path / "raw" / "20210305_NE_mockData1"
        )
        imc.create_panel_from_mcd_files(mcd_files)  # TODO

    def test_create_panel_from_txt_file(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_create_panel_from_txt_files(self, imc_test_data_steinbock_path: Path):
        txt_files = imc.list_txt_files(
            imc_test_data_steinbock_path / "raw" / "20210305_NE_mockData1"
        )
        imc.create_panel_from_txt_files(txt_files)  # TODO

    def test_create_image_info(self, imc_test_data_steinbock_path: Path):
        pass  # TODO

    def test_filter_hot_pixels(self):
        img = np.array(
            [
                [
                    [1, 2, 3],
                    [4, 13, 6],
                    [7, 8, 9],
                ]
            ],
            dtype=io.img_dtype,
        )
        filtered_img = imc.filter_hot_pixels(img, 3.0)
        expected_filtered_img = np.array(
            [
                [
                    [1, 2, 3],
                    [4, 9, 6],
                    [7, 8, 9],
                ]
            ],
            dtype=io.img_dtype,
        )
        assert np.all(filtered_img == expected_filtered_img)

    def test_preprocess_image(self):
        img = np.array(
            [
                [
                    [1, 2, 3],
                    [4, 13, 6],
                    [7, 8, 9],
                ],
            ],
            dtype=io.img_dtype,
        )
        preprocessed_img = imc.preprocess_image(img, hpf=3.0)
        expected_preprocessed_img = np.array(
            [
                [
                    [1, 2, 3],
                    [4, 9, 6],
                    [7, 8, 9],
                ]
            ],
            dtype=io.img_dtype,
        )
        assert np.all(preprocessed_img == expected_preprocessed_img)

    def test_try_preprocess_images_from_disk(self, imc_test_data_steinbock_path: Path):
        mcd_files = imc.list_mcd_files(imc_test_data_steinbock_path / "raw")
        txt_files = imc.list_txt_files(imc_test_data_steinbock_path / "raw")
        gen = imc.try_preprocess_images_from_disk(mcd_files, txt_files)
        for mcd_txt_file, acquisition, img, recovery_file, recovered in gen:
            pass  # TODO


@pytest.mark.skipif(not imc.imc_available, reason="IMC is not available")
def test_images_cmd_duplicate_file_names(
    imc_test_data_steinbock_path: Path, tmp_path: Path
):
    txt_file = next((imc_test_data_steinbock_path / "raw").rglob("*.txt"))
    raw_dir = tmp_path / "raw"
    for run in ("run1", "run2", "run3"):
        (raw_dir / run).mkdir(parents=True)
        shutil.copy(txt_file, raw_dir / run)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            steinbock_cmd_group,
            [
                "preprocess",
                "imc",
                "images",
                "--mcd",
                str(raw_dir),
                "--txt",
                str(raw_dir),
            ],
        )
        assert result.exit_code == 0, result.output
        assert sorted(p.name for p in Path("img").glob("*.tiff")) == sorted(
            [
                f"{txt_file.stem}.tiff",
                f"DUPLICATE001_{txt_file.stem}.tiff",
                f"DUPLICATE002_{txt_file.stem}.tiff",
            ]
        )
        assert len(io.read_image_info("images.csv")) == 3
