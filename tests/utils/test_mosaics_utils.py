from pathlib import Path

from steinbock import io
from steinbock.utils import mosaics


class TestMosaicsUtils:
    def test_try_extract_tiles_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
        gen = mosaics.try_extract_tiles_from_disk(img_files, 50)
        for img_file, tile_file_stem, tile in gen:
            pass  # TODO

    def test_try_stitch_tiles_from_disk(
        self, imc_test_data_steinbock_path: Path, tmp_path: Path
    ):
        img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
        tile_files = []
        gen = mosaics.try_extract_tiles_from_disk(img_files, 50)
        for img_file, tile_file_stem, tile in gen:
            tile_file = tmp_path / f"{tile_file_stem}.tiff"
            io.write_image(tile, tile_file, ignore_dtype=True)
            tile_files.append(tile_file)
            del tile
        gen = mosaics.try_stitch_tiles_from_disk(tile_files)
        for img_file_stem, img in gen:
            pass  # TODO
