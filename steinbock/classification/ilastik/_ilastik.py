import cv2
import h5py
import json
import logging
import numpy as np

import shutil
import subprocess

from enum import IntEnum
from os import PathLike
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)
from uuid import uuid1

from steinbock import io
from steinbock._env import run_captured


class _VigraAxisInfo(IntEnum):
    CHANNELS = 1
    SPACE = 2
    ANGLE = 4
    TIME = 8
    FREQUENCY = 16
    EDGE = 32
    UNKNOWN_AXIS_TYPE = 64


_logger = logging.getLogger(__name__)

_img_dataset_path = "img"
_crop_dataset_path = "crop"
_dataset_display_mode = "grayscale"
_project_file_template = (
    Path(__file__).parent / "data" / "pixel_classifier.ilp"
)
_dataset_axistags = json.dumps(
    {
        "axes": [
            {"key": "c", "typeFlags": _VigraAxisInfo.CHANNELS.value},
            {"key": "y", "typeFlags": _VigraAxisInfo.SPACE.value},
            {"key": "x", "typeFlags": _VigraAxisInfo.SPACE.value},
        ]
    }
)
_h5py_libver = "earliest"


def list_ilastik_image_files(
    ilastik_img_dir: Union[str, PathLike]
) -> List[Path]:
    return sorted(Path(ilastik_img_dir).rglob("*.h5"))


def list_ilastik_crop_files(
    ilastik_crop_dir: Union[str, PathLike]
) -> List[Path]:
    return sorted(Path(ilastik_crop_dir).rglob("*.h5"))


def read_ilastik_image(ilastik_img_stem: Union[str, PathLike]) -> np.ndarray:
    ilastik_img_file = io._as_path_with_suffix(ilastik_img_stem, ".h5")
    with h5py.File(ilastik_img_file, mode="r", libver=_h5py_libver) as f:
        return io._to_dtype(f[str(_img_dataset_path)][()], io.img_dtype)


def read_ilastik_crop(ilastik_crop_stem: Union[str, PathLike]) -> np.ndarray:
    ilastik_crop_file = io._as_path_with_suffix(ilastik_crop_stem, ".h5")
    with h5py.File(ilastik_crop_file, mode="r", libver=_h5py_libver) as f:
        return io._to_dtype(f[str(_crop_dataset_path)][()], io.img_dtype)


def write_ilastik_image(
    ilastik_img: np.ndarray, ilastik_img_stem: Union[str, PathLike]
) -> Path:
    ilastik_img = io._to_dtype(ilastik_img, io.img_dtype)
    ilastik_img_file = io._as_path_with_suffix(ilastik_img_stem, ".h5")
    with h5py.File(ilastik_img_file, mode="w", libver=_h5py_libver) as f:
        dataset = _create_or_replace_dataset(f, _img_dataset_path, ilastik_img)
        dataset.attrs["display_mode"] = _str_encode(
            _dataset_display_mode, ascii=True
        )
        dataset.attrs["axistags"] = _str_encode(_dataset_axistags, ascii=True)
        dataset.attrs["steinbock"] = True
    return ilastik_img_file


def write_ilastik_crop(
    ilastik_crop: np.ndarray, ilastik_crop_stem: Union[str, PathLike]
):
    ilastik_crop = io._to_dtype(ilastik_crop, io.img_dtype)
    ilastik_crop_file = io._as_path_with_suffix(ilastik_crop_stem, ".h5")
    with h5py.File(ilastik_crop_file, mode="w", libver=_h5py_libver) as f:
        dataset = _create_or_replace_dataset(
            f, _crop_dataset_path, ilastik_crop
        )
        dataset.attrs["display_mode"] = _str_encode(
            _dataset_display_mode, ascii=True
        )
        dataset.attrs["axistags"] = _str_encode(_dataset_axistags, ascii=True)
        dataset.attrs["steinbock"] = True
    return ilastik_crop_file


def create_ilastik_image(
    img: np.ndarray,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: Callable[[np.ndarray], np.ndarray] = np.mean,
    prepend_mean: bool = True,
    mean_factor: float = 100.0,
    scale_factor: int = 1,
) -> np.ndarray:
    ilastik_img = img
    if channel_groups is not None:
        ilastik_img = np.stack(
            [
                aggr_func(ilastik_img[channel_groups == channel_group], axis=0)
                for channel_group in np.unique(channel_groups)
                if not np.isnan(channel_group)
            ]
        )
    if prepend_mean:
        mean_img = ilastik_img.mean(axis=0, keepdims=True) * mean_factor
        ilastik_img = np.concatenate((mean_img, ilastik_img))
    if scale_factor > 1:
        # bilinear resizing (for compatibility with IMC Segmentation Pipeline)
        # # use OpenCV instead of scikit-image for memory reasons
        # output_shape = (
        #     ilastik_img.shape[0],
        #     ilastik_img.shape[1] * scale_factor,
        #     ilastik_img.shape[2] * scale_factor,
        # )
        # ilastik_img = resize(
        #     ilastik_img, output_shape, order=1, mode="symmetric"
        # )
        ilastik_img = np.stack(
            [
                cv2.resize(
                    ilastik_channel_img,
                    None,
                    fx=scale_factor,
                    fy=scale_factor,
                    interpolation=cv2.INTER_LINEAR,
                )
                for ilastik_channel_img in ilastik_img
            ]
        )

    return io._to_dtype(ilastik_img, io.img_dtype)


def try_create_ilastik_images_from_disk(
    img_files: Sequence[Union[str, PathLike]],
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: Callable[[np.ndarray], np.ndarray] = np.mean,
    prepend_mean: bool = True,
    mean_factor: float = 100.0,
    scale_factor: int = 1,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for img_file in img_files:
        try:
            ilastik_img = create_ilastik_image(
                io.read_image(img_file, native_dtype=True),
                channel_groups=channel_groups,
                aggr_func=aggr_func,
                prepend_mean=prepend_mean,
                mean_factor=mean_factor,
                scale_factor=scale_factor,
            )
            yield Path(img_file), ilastik_img
            del ilastik_img
        except:
            _logger.exception(
                f"Error creating Ilastik image from file {img_file}"
            )


def create_ilastik_crop(
    ilastik_img: np.ndarray, ilastik_crop_size: int, rng: np.random.Generator
) -> Tuple[Optional[int], Optional[int], Optional[np.ndarray]]:
    if all(shape >= ilastik_crop_size for shape in ilastik_img.shape[1:]):
        ilastik_crop_x = 0
        if ilastik_img.shape[2] > ilastik_crop_size:
            ilastik_crop_x = rng.integers(
                ilastik_img.shape[2] - ilastik_crop_size
            )
        ilastik_crop_y = 0
        if ilastik_img.shape[1] > ilastik_crop_size:
            ilastik_crop_y = rng.integers(
                ilastik_img.shape[1] - ilastik_crop_size
            )
        ilastik_crop = ilastik_img[
            :,
            ilastik_crop_y : (ilastik_crop_y + ilastik_crop_size),
            ilastik_crop_x : (ilastik_crop_x + ilastik_crop_size),
        ]
        return (
            ilastik_crop_x,
            ilastik_crop_y,
            io._to_dtype(ilastik_crop, io.img_dtype),
        )
    return None, None, None


def try_create_ilastik_crops_from_disk(
    ilastik_img_files: Sequence[Union[str, PathLike]],
    ilastik_crop_size: int,
    rng: np.random.Generator,
) -> Generator[
    Tuple[Path, Optional[int], Optional[int], Optional[np.ndarray]],
    None,
    None,
]:
    for ilastik_img_file in ilastik_img_files:
        try:
            ilastik_crop_x, ilastik_crop_y, ilastik_crop = create_ilastik_crop(
                read_ilastik_image(ilastik_img_file), ilastik_crop_size, rng
            )
            yield Path(
                ilastik_img_file
            ), ilastik_crop_x, ilastik_crop_y, ilastik_crop
            del ilastik_crop
        except:
            _logger.exception(
                f"Error creating Ilastik crop from file {ilastik_img_file}"
            )


def create_and_save_ilastik_project(
    ilastik_crop_files: Sequence[Union[str, PathLike]],
    ilastik_project_file: Union[str, PathLike],
):
    dataset_id = str(uuid1())
    shutil.copyfile(_project_file_template, ilastik_project_file)
    with h5py.File(ilastik_project_file, mode="a", libver=_h5py_libver) as f:
        infos_group = f["Input Data/infos"]
        for i, ilastik_crop_file in enumerate(ilastik_crop_files):
            rel_ilastik_crop_file = Path(ilastik_crop_file).relative_to(
                Path(ilastik_project_file).parent
            )
            with h5py.File(
                ilastik_crop_file, mode="r", libver=_h5py_libver
            ) as f_crop:
                ilastik_crop_shape = f_crop[_crop_dataset_path].shape
            lane_group = infos_group.create_group(f"lane{i:04d}")
            lane_group.create_group("Prediction Mask")
            raw_data_group = lane_group.create_group("Raw Data")
            _fix_raw_data_group_inplace(
                raw_data_group,
                dataset_id=dataset_id,
                file_path=str(rel_ilastik_crop_file / _crop_dataset_path),
                nickname=Path(ilastik_crop_file).stem,
                shape=ilastik_crop_shape,
            )


def run_pixel_classification(
    ilastik_binary: Union[str, PathLike],
    ilastik_project_file: Union[str, PathLike],
    ilastik_img_files: Sequence[Union[str, PathLike]],
    ilastik_probab_dir: Union[str, PathLike],
    num_threads: Optional[int] = None,
    memory_limit: Optional[int] = None,
    ilastik_env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    output_filename_format = Path(ilastik_probab_dir) / "{nickname}.tiff"
    args = [
        str(ilastik_binary),
        "--headless",
        f"--project={ilastik_project_file}",
        "--readonly",
        "--input_axes=cyx",
        "--export_source=Probabilities",
        "--output_format=tiff",
        f"--output_filename_format={output_filename_format}",
        "--export_dtype=uint16",
        "--output_axis_order=yxc",
        "--pipeline_result_drange=(0.0,1.0)",
        "--export_drange=(0,65535)",
    ]
    for ilastik_img_file in ilastik_img_files:
        args.append(str(Path(ilastik_img_file) / _img_dataset_path))
    if ilastik_env is not None:
        ilastik_env = ilastik_env.copy()
        if num_threads is not None:
            ilastik_env["LAZYFLOW_THREADS"] = num_threads
        if memory_limit is not None:
            ilastik_env["LAZYFLOW_TOTAL_RAM_MB"] = memory_limit
    result = run_captured(args, env=ilastik_env)
    ilastik_probab_files = Path(ilastik_probab_dir).rglob(
        f"*-{_img_dataset_path}.tiff"
    )
    for ilastik_probab_file in sorted(ilastik_probab_files):
        ilastik_probab_file.rename(
            ilastik_probab_file.with_name(
                ilastik_probab_file.name.replace(f"-{_img_dataset_path}", "")
            )
        )
    return result


def try_fix_ilastik_crops_from_disk(
    ilastik_crop_files: Sequence[Union[str, PathLike]],
    orig_axis_order: Union[str, Sequence, None] = None,
) -> Generator[Tuple[Path, Tuple[int, ...], np.ndarray], None, None]:
    for ilastik_crop_file in ilastik_crop_files:
        try:
            with h5py.File(
                ilastik_crop_file, mode="r", libver=_h5py_libver
            ) as f:
                ilastik_crop_dataset = None
                if _crop_dataset_path in f:
                    ilastik_crop_dataset = f[_crop_dataset_path]
                elif Path(ilastik_crop_file).stem in f:
                    ilastik_crop_dataset = f[Path(ilastik_crop_file).stem]
                elif len(f) == 1:
                    ilastik_crop_dataset = next(iter(f.values()))
                else:
                    raise ValueError(f"Unknown dataset: {ilastik_crop_file}")
                if ilastik_crop_dataset.attrs.get("steinbock", False):
                    continue
                ilastik_crop = ilastik_crop_dataset[()]
                if orig_axis_order is not None:
                    orig_axis_order = list(orig_axis_order)
                elif "axistags" in ilastik_crop_dataset.attrs:
                    axis_tags, _ = _str_decode(
                        ilastik_crop_dataset.attrs["axistags"]
                    )
                    axis_tags_json = json.loads(axis_tags)
                    orig_axis_order = [
                        a_json["key"] for a_json in axis_tags_json["axes"]
                    ]
                else:
                    raise ValueError(
                        f"Unknown axis order: {ilastik_crop_file}"
                    )
            if len(orig_axis_order) != ilastik_crop.ndim:
                raise ValueError(
                    f"Incompatible axis order: {ilastik_crop_file}"
                )
            channel_axis_index = orig_axis_order.index("c")
            num_channels = ilastik_crop.size // (
                ilastik_crop.shape[orig_axis_order.index("x")]
                * ilastik_crop.shape[orig_axis_order.index("y")]
            )
            if ilastik_crop.shape[channel_axis_index] != num_channels:
                channel_axis_indices = (
                    i
                    for i, a in enumerate(orig_axis_order)
                    if ilastik_crop.shape[i] == num_channels
                    and a not in ("x", "y")
                )
                channel_axis_index = next(channel_axis_indices, None)
            if channel_axis_index is None:
                raise ValueError(f"Unknown channel axis: {ilastik_crop_file}")
            axis_order = orig_axis_order.copy()
            axis_order.insert(0, axis_order.pop(channel_axis_index))
            axis_order.insert(1, axis_order.pop(axis_order.index("y")))
            axis_order.insert(2, axis_order.pop(axis_order.index("x")))
            transpose_axes = [orig_axis_order.index(a) for a in axis_order]
            ilastik_crop = np.transpose(ilastik_crop, axes=transpose_axes)
            ilastik_crop = np.reshape(ilastik_crop, ilastik_crop.shape[:3])
            ilastik_crop = io._to_dtype(ilastik_crop, io.img_dtype)
            yield Path(ilastik_crop_file), transpose_axes, ilastik_crop
            del ilastik_crop
        except:
            _logger.exception(
                f"Error fixing Ilastik crop from file {ilastik_crop_file}"
            )


def fix_ilastik_project_file_inplace(
    ilastik_project_file: Union[str, PathLike],
    ilastik_crop_dir: Union[str, PathLike],
    ilastik_probab_dir: Union[str, PathLike],
    ilastik_crop_shapes: Dict[str, Tuple[int, ...]],
    transpose_axes: List[int],
):
    rel_ilastik_crop_dir = Path(ilastik_crop_dir).relative_to(
        Path(ilastik_project_file).parent
    )
    rel_ilastik_probab_dir = Path(ilastik_probab_dir).relative_to(
        Path(ilastik_project_file).parent
    )
    with h5py.File(ilastik_project_file, "a", libver=_h5py_libver) as f:
        input_data_group = f.get("Input Data")
        if input_data_group is not None:
            _fix_input_data_group_inplace(
                input_data_group, rel_ilastik_crop_dir, ilastik_crop_shapes
            )
        pixel_classification_group = f.get("PixelClassification")
        if pixel_classification_group is not None:
            _fix_pixel_classification_group_inplace(
                pixel_classification_group, transpose_axes
            )
        prediction_export_group = f["Prediction Export"]
        if prediction_export_group is not None:
            _fix_prediction_export_group_inplace(
                prediction_export_group, rel_ilastik_probab_dir
            )


def _fix_input_data_group_inplace(
    input_data_group: h5py.Group,
    rel_ilastik_crop_dir: Path,
    ilastik_crop_shapes: Dict[str, Tuple[int, ...]],
):
    infos_group = input_data_group.get("infos")
    if infos_group is not None:
        for lane_group in infos_group.values():
            raw_data_group = lane_group.get("Raw Data")
            if raw_data_group is not None:
                file_path, _ = _str_decode(raw_data_group["filePath"][()])
                ilastik_crop_file = _get_hdf5_file(file_path)
                _fix_raw_data_group_inplace(
                    raw_data_group,
                    file_path=str(
                        rel_ilastik_crop_dir
                        / ilastik_crop_file.name
                        / _crop_dataset_path
                    ),
                    nickname=ilastik_crop_file.stem,
                    shape=ilastik_crop_shapes[ilastik_crop_file.stem],
                )
    local_data_group = input_data_group.get("local_data")
    if local_data_group is not None:
        local_data_group.clear()


def _fix_pixel_classification_group_inplace(
    pixel_classification_group: h5py.Group, transpose_axes: List[int]
):
    label_sets_group = pixel_classification_group.get("LabelSets")
    if label_sets_group is not None:
        for labels_group in label_sets_group.values():
            block_dataset_names = list(labels_group.keys())
            for block_dataset_name in block_dataset_names:
                block_dataset = labels_group[block_dataset_name]
                block = block_dataset[()]
                block = np.transpose(block, axes=transpose_axes)
                block = np.reshape(block, block.shape[:3])
                block_slice, block_slice_ascii = _str_decode(
                    block_dataset.attrs["blockSlice"]
                )
                block_slice = block_slice[1:-1].split(",")
                block_slice = [block_slice[i] for i in transpose_axes[:3]]
                block_slice = f"[{','.join(block_slice)}]"
                del labels_group[block_dataset_name]
                block_dataset = _create_or_replace_dataset(
                    labels_group, block_dataset_name, block
                )
                block_dataset.attrs["blockSlice"] = _str_encode(
                    block_slice, ascii=block_slice_ascii
                )


def _fix_prediction_export_group_inplace(
    prediction_export_group: h5py.Group, rel_ilastik_probab_dir: Path
):
    _logger.warning(
        "When exporting data from the graphical user interface of Ilastik, "
        "please manually edit the export image settings and enable "
        "renormalizing [min, max] from [0.0, 1.0] to [0, 65535]"
    )
    # _create_or_replace_dataset(
    #   prediction_export_group,
    #   "InputMin",
    #   np.array([0.0], dtype=np.float32),
    # )
    # _create_or_replace_dataset(
    #   prediction_export_group,
    #   "InputMax", np.array([1.0], dtype=np.float32),
    # )
    _create_or_replace_dataset(
        prediction_export_group, "ExportMin", np.array([0], dtype=np.uint16)
    )
    _create_or_replace_dataset(
        prediction_export_group,
        "ExportMax",
        np.array([65535], dtype=np.uint16),
    )
    _create_or_replace_dataset(
        prediction_export_group, "ExportDtype", "uint16", ascii=False
    )
    _create_or_replace_dataset(
        prediction_export_group, "OutputAxisOrder", "yxc", ascii=True
    )
    _create_or_replace_dataset(
        prediction_export_group, "OutputFormat", "tiff", ascii=True
    )
    _create_or_replace_dataset(
        prediction_export_group,
        "OutputFilenameFormat",
        f"{rel_ilastik_probab_dir}/{{nickname}}.tiff",
        ascii=True,
    )
    _create_or_replace_dataset(
        prediction_export_group,
        "OutputInternalPath",
        "exported_data",
        ascii=True,
    )
    _create_or_replace_dataset(
        prediction_export_group, "StorageVersion", "0.1", ascii=False
    )


def _fix_raw_data_group_inplace(
    raw_data_group: h5py.Group,
    dataset_id: Optional[str] = None,
    file_path: Optional[str] = None,
    nickname: Optional[str] = None,
    shape: Optional[Tuple[int, ...]] = None,
):
    _create_or_replace_dataset(
        raw_data_group,
        "__class__",
        "RelativeFilesystemDatasetInfo",
        ascii=True,
    )
    _create_or_replace_dataset(raw_data_group, "allowLabels", True)
    _create_or_replace_dataset(
        raw_data_group, "axistags", _dataset_axistags, ascii=True
    )
    if dataset_id is not None:
        _create_or_replace_dataset(
            raw_data_group, "datasetId", dataset_id, ascii=True
        )
    _create_or_replace_dataset(
        raw_data_group, "display_mode", _dataset_display_mode, ascii=True
    )
    if file_path is not None:
        _create_or_replace_dataset(
            raw_data_group, "filePath", file_path, ascii=True
        )
    _create_or_replace_dataset(
        raw_data_group, "location", "FileSystem", ascii=True
    )
    if nickname is not None:
        _create_or_replace_dataset(
            raw_data_group, "nickname", nickname, ascii=True
        )
    _create_or_replace_dataset(raw_data_group, "normalizeDisplay", False)
    if shape is not None:
        _create_or_replace_dataset(
            raw_data_group, "shape", data=np.array(shape, dtype=np.int64)
        )


def _get_hdf5_file(hdf5_path: Union[str, PathLike]) -> Optional[Path]:
    hdf5_file = hdf5_path
    while hdf5_file is not None and Path(hdf5_file).suffix != ".h5":
        hdf5_file = Path(hdf5_file).parent
    return hdf5_file


def _str_decode(obj: Union[str, bytes]) -> Tuple[str, bool]:
    if isinstance(obj, bytes):
        return obj.decode("ascii"), True
    return obj, False


def _str_encode(obj: str, ascii: bool = False) -> Union[str, bytes]:
    if ascii and isinstance(obj, str):
        return obj.encode("ascii")
    return obj


def _create_or_replace_dataset(
    parent: Union[h5py.File, h5py.Group],
    key: str,
    data: Union[str, Any],
    ascii: bool = True,
) -> h5py.Dataset:
    old_dataset = parent.get(key)
    if old_dataset is not None:
        old_data = old_dataset[()]
        if isinstance(old_data, str):
            _, ascii = _str_decode(old_data)
        del parent[key]
    if isinstance(data, str):
        data = _str_encode(data, ascii=ascii)
    return parent.create_dataset(key, data=data)
