# from pathlib import Path

# from steinbock import io
# from steinbock.utils import mosaics


# class TestMosaicsUtils:
#     def test_try_extract_tiles_from_disk(
#         self, imc_test_data_steinbock_path: Path
#     ):
#         img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
#         gen = mosaics.try_extract_tiles_from_disk(img_files, 50)
#         for img_file, tile_info, tile in gen:
#             pass  # TODO

#     def test_try_stitch_tiles_from_disk(
#         self, imc_test_data_steinbock_path: Path, tmp_path: Path
#     ):
#         img_files = io.list_image_files(imc_test_data_steinbock_path / "img")
#         img_file_stems = []
#         img_tile_files = {}
#         img_tile_infos = {}
#         gen = mosaics.try_extract_tiles_from_disk(img_files, 50)
#         for img_file, tile_info, tile in gen:
#             tile_file = tmp_path / (
#                 f"{tile_info.img_file_stem}_tx{tile_info.x}_ty{tile_info.y}"
#                 f"_tw{tile_info.width}_th{tile_info.height}.tiff"
#             )
#             if tile_info.img_file_stem not in img_file_stems:
#                 img_file_stems.append(tile_info.img_file_stem)
#                 img_tile_files[tile_info.img_file_stem] = []
#                 img_tile_infos[tile_info.img_file_stem] = []
#             img_tile_files[tile_info.img_file_stem].append(tile_file)
#             img_tile_infos[tile_info.img_file_stem].append(tile_info)
#             io.write_image(tile, tile_file, ignore_dtype=True)
#             del tile
#         gen = mosaics.try_stitch_tiles_from_disk(
#             img_file_stems, img_tile_files, img_tile_infos
#         )
#         for img_file_stem, img in gen:
#             pass  # TODO
