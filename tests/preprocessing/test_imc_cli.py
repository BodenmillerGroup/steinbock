import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from steinbock._cli import steinbock_cmd_group
from steinbock.preprocessing import imc


def run_images(runner: CliRunner, *args: str):
    return runner.invoke(steinbock_cmd_group, ["preprocess", "imc", "images", *args])


@pytest.mark.skipif(not imc.imc_available, reason="IMC is not available")
class TestIMCImagesCommand:
    def test_txt_only(self, imc_test_data_steinbock_path: Path, tmp_path: Path):
        txt_dir = tmp_path / "txt"
        txt_dir.mkdir()
        for txt_file in (imc_test_data_steinbock_path / "raw").rglob("*.txt"):
            shutil.copy(txt_file, txt_dir)
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = run_images(runner, "--txt", str(txt_dir))
            assert result.exit_code == 0, result.output
            assert len(list(Path("img").glob("*.tiff"))) == len(
                list(txt_dir.glob("*.txt"))
            )

    def test_missing_dir_given_by_user(self, tmp_path: Path):
        txt_dir = tmp_path / "txt"
        txt_dir.mkdir()
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = run_images(runner, "--txt", str(txt_dir), "--mcd", "missing")
            assert result.exit_code != 0
            assert "'missing' does not exist" in result.output

    def test_no_files(self, tmp_path: Path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = run_images(runner)
            assert result.exit_code != 0
            assert "No .mcd/.txt files found" in result.output
