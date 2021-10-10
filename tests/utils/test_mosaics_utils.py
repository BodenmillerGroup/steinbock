from pathlib import Path

from steinbock import io
from steinbock.utils import mosaics


class TestMosaicsUtils:
    def test_try_extract_tiles_from_disk(
        self, imc_test_data_steinbock_path: Path
    ):
        img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
        gen = mosaics.try_extract_tiles_from_disk(img_files, 50)
        for img_file, x, y, tile in gen:
            pass  # TODO

    def test_try_stitch_tiles_from_disk(
        self, imc_test_data_steinbock_path: Path, tmp_path: Path
    ):
        tile_info_groups = {}
        img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
        gen = mosaics.try_extract_tiles_from_disk(img_files, 50)
        for img_file, x, y, tile in gen:
            tile_stem = tmp_path / f"{img_file.stem}_tx{x}_ty{y}_tw50_th50"
            io.write_image(tile, tile_stem, ignore_dtype=True)
            if img_file.stem not in tile_info_groups:
                tile_info_groups[img_file.stem] = []
            tile_info_groups[img_file.stem].append((img_file, x, y, 50, 50))
            del tile
        gen = mosaics.try_stitch_tiles_from_disk(tile_info_groups)
        for img_stem, img in gen:
            pass  # TODO
