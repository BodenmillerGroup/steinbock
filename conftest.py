import pytest
import requests
import shutil

from pathlib import Path
from typing import Generator


_imc_test_data_steinbock_url = (
    "https://github.com/BodenmillerGroup/TestData"
    "/releases/download/v1.0.7/210308_ImcTestData_steinbock.tar.gz"
)
_imc_test_data_steinbock_dir = "datasets/210308_ImcTestData/steinbock"


def _download_and_extract_asset(tmp_dir_path: Path, asset_url: str):
    asset_file_path = tmp_dir_path / "asset.tar.gz"
    response = requests.get(asset_url, stream=True)
    if response.status_code == 200:
        with asset_file_path.open(mode="wb") as f:
            f.write(response.raw.read())
    shutil.unpack_archive(asset_file_path, tmp_dir_path)


@pytest.fixture(scope="session")
def imc_test_data_steinbock_path(
    tmp_path_factory,
) -> Generator[Path, None, None]:
    tmp_dir_path = tmp_path_factory.mktemp("raw")
    _download_and_extract_asset(tmp_dir_path, _imc_test_data_steinbock_url)
    yield tmp_dir_path / Path(_imc_test_data_steinbock_dir)
    shutil.rmtree(tmp_dir_path)
