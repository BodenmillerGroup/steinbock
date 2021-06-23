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
_h5py_libver = "latest"


def list_ilastik_image_files(img_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(img_dir).rglob("*.h5"))


def list_ilastik_crop_files(crop_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(crop_dir).rglob("*.h5"))


def read_ilastik_image(ilastik_img_stem: Union[str, PathLike]) -> np.ndarray:
    ilastik_img_file = Path(ilastik_img_stem).with_suffix(".h5")
    with h5py.File(ilastik_img_file, mode="r", libver=_h5py_libver) as f:
        return f[str(_img_dataset_path)][()]


def read_ilastik_crop(ilastik_crop_stem: Union[str, PathLike]) -> np.ndarray:
    ilastik_crop_file = Path(ilastik_crop_stem).with_suffix(".h5")
    with h5py.File(ilastik_crop_file, mode="r", libver=_h5py_libver) as f:
        return f[str(_crop_dataset_path)][()]


def write_ilastik_image(
    ilastik_img: np.ndarray, ilastik_img_stem: Union[str, PathLike]
) -> Path:
    ilastik_img_file = Path(ilastik_img_stem).with_suffix(".h5")
    with h5py.File(ilastik_img_file, mode="w", libver=_h5py_libver) as f:
        dataset = f.create_dataset(_img_dataset_path, data=ilastik_img)
        dataset.attrs["display_mode"] = _dataset_display_mode.encode("ascii")
        dataset.attrs["axistags"] = _dataset_axistags.encode("ascii")
        dataset.attrs["steinbock"] = True
    return ilastik_img_file


def write_ilastik_crop(
    ilastik_crop: np.ndarray, ilastik_crop_stem: Union[str, PathLike]
):
    ilastik_crop_file = Path(ilastik_crop_stem).with_suffix(".h5")
    with h5py.File(ilastik_crop_file, mode="w", libver=_h5py_libver) as f:
        dataset = f.create_dataset(_crop_dataset_path, data=ilastik_crop)
        dataset.attrs["display_mode"] = _dataset_display_mode.encode("ascii")
        dataset.attrs["axistags"] = _dataset_axistags.encode("ascii")
        dataset.attrs["steinbock"] = True
    return ilastik_crop_file


def create_ilastik_image(
    img: np.ndarray,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: Callable[[np.ndarray], np.ndarray] = np.mean,
    prepend_mean: bool = True,
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
        mean_img = ilastik_img.mean(axis=0, keepdims=True)
        ilastik_img = np.concatenate((mean_img, ilastik_img))
    if scale_factor > 1:
        ilastik_img = ilastik_img.repeat(scale_factor, axis=1)
        ilastik_img = ilastik_img.repeat(scale_factor, axis=2)
    return ilastik_img


def create_ilastik_images_from_disk(
    img_files: Sequence[Union[str, PathLike]],
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: Callable[[np.ndarray], np.ndarray] = np.mean,
    prepend_mean: bool = True,
    scale_factor: int = 1,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for img_file in img_files:
        ilastik_img = create_ilastik_image(
            io.read_image(img_file),
            channel_groups=channel_groups,
            aggr_func=aggr_func,
            prepend_mean=prepend_mean,
            scale_factor=scale_factor,
        )
        yield Path(img_file), ilastik_img
        del ilastik_img


def create_ilastik_crop(
    ilastik_img: np.ndarray, crop_size: int, rng: np.random.Generator
) -> Tuple[Optional[int], Optional[int], Optional[np.ndarray]]:
    yx_shape = ilastik_img.shape[1:]
    if all(shape >= crop_size for shape in yx_shape):
        x_start = rng.integers(ilastik_img.shape[2] - crop_size)
        x_end = x_start + crop_size
        y_start = rng.integers(ilastik_img.shape[1] - crop_size)
        y_end = y_start + crop_size
        ilastik_crop = ilastik_img[:, y_start:y_end, x_start:x_end]
        return x_start, y_start, ilastik_crop
    return None, None, None


def create_ilastik_crops_from_disk(
    ilastik_img_files: Sequence[Union[str, PathLike]],
    crop_size: int,
    seed=None,
) -> Generator[
    Tuple[Path, Optional[int], Optional[int], Optional[np.ndarray]],
    None,
    None,
]:
    rng = np.random.default_rng(seed=seed)
    for ilastik_img_file in ilastik_img_files:
        x_start, y_start, ilastik_crop = create_ilastik_crop(
            read_ilastik_image(ilastik_img_file), crop_size, rng,
        )
        yield Path(ilastik_img_file), x_start, y_start, ilastik_crop
        del ilastik_crop


def create_and_save_ilastik_project(
    ilastik_crop_files: Sequence[Union[str, PathLike]],
    ilastik_project_file: Union[str, PathLike],
):
    dataset_id = str(uuid1())
    shutil.copyfile(_project_file_template, ilastik_project_file)
    with h5py.File(ilastik_project_file, mode="a", libver=_h5py_libver) as f:
        infos = f["Input Data/infos"]
        for i, ilastik_crop_file in enumerate(ilastik_crop_files):
            rel_ilastik_crop_file = Path(ilastik_crop_file).relative_to(
                Path(ilastik_project_file).parent
            )
            with h5py.File(
                ilastik_crop_file, mode="r", libver=_h5py_libver
            ) as f_crop:
                crop_shape = f_crop[_crop_dataset_path].shape
            lane = infos.create_group(f"lane{i:04d}")
            lane.create_group("Prediction Mask")
            _init_project_raw_data_group(
                lane.create_group("Raw Data"),
                dataset_id,
                str(rel_ilastik_crop_file / _crop_dataset_path),
                Path(ilastik_crop_file).stem,
                crop_shape,
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


def fix_ilastik_crops_from_disk(
    ilastik_crop_files: Sequence[Union[str, PathLike]],
    axis_order: Optional[str] = None,
) -> Generator[Tuple[Path, Tuple[int, ...], np.ndarray], None, None]:
    for ilastik_crop_file in ilastik_crop_files:
        with h5py.File(ilastik_crop_file, mode="r", libver=_h5py_libver) as f:
            ilastik_crop_dataset = None
            if _crop_dataset_path in f:
                ilastik_crop_dataset = f[_crop_dataset_path]
            elif ilastik_crop_file.stem in f:
                ilastik_crop_dataset = f[ilastik_crop_file.stem]
            elif len(f) == 1:
                ilastik_crop_dataset = next(iter(f.values()))
            else:
                raise ValueError(f"Unknown dataset name: {ilastik_crop_file}")
            if ilastik_crop_dataset.attrs.get("steinbock", False):
                continue
            ilastik_crop = ilastik_crop_dataset[()]
            orig_axis_order = None
            if axis_order is not None:
                orig_axis_order = list(axis_order)
            elif "axistags" in ilastik_crop_dataset.attrs:
                axis_tags = json.loads(ilastik_crop_dataset.attrs["axistags"])
                orig_axis_order = [item["key"] for item in axis_tags["axes"]]
            else:
                raise ValueError(f"Unknown axis order: {ilastik_crop_file}")
        if len(orig_axis_order) != ilastik_crop.ndim:
            raise ValueError(f"Incompatible axis order: {ilastik_crop_file}")
        channel_axis_index = orig_axis_order.index("c")
        size_x = ilastik_crop.shape[orig_axis_order.index("x")]
        size_y = ilastik_crop.shape[orig_axis_order.index("y")]
        num_channels = ilastik_crop.size // (size_x * size_y)
        if ilastik_crop.shape[channel_axis_index] != num_channels:
            channel_axis_indices = (
                i
                for i, a in enumerate(orig_axis_order)
                if a not in ("x", "y")
                and ilastik_crop.shape[i] == num_channels
            )
            channel_axis_index = next(channel_axis_indices, None)
        if channel_axis_index is None:
            raise ValueError(f"Unknown channel axis: {ilastik_crop_file}")
        new_axis_order = orig_axis_order.copy()
        new_axis_order.insert(0, new_axis_order.pop(channel_axis_index))
        new_axis_order.insert(1, new_axis_order.pop(new_axis_order.index("y")))
        new_axis_order.insert(2, new_axis_order.pop(new_axis_order.index("x")))
        transpose_axes = [orig_axis_order.index(a) for a in new_axis_order]
        ilastik_crop = np.transpose(ilastik_crop, axes=transpose_axes)
        ilastik_crop = np.reshape(ilastik_crop, ilastik_crop.shape[:3])
        ilastik_crop = ilastik_crop.astype(np.float32)
        yield Path(ilastik_crop_file), transpose_axes, ilastik_crop
        del ilastik_crop


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
        if "Input Data" in f:
            _fix_project_input_data_inplace(
                f["Input Data"], rel_ilastik_crop_dir, ilastik_crop_shapes
            )
        if "PixelClassification" in f:
            _fix_project_pixel_classification_inplace(
                f["PixelClassification"], transpose_axes
            )
        if "Prediction Export" in f:
            _fix_project_prediction_export_inplace(
                f["Prediction Export"], rel_ilastik_probab_dir
            )


def _fix_project_input_data_inplace(
    input_data_group: h5py.Group,
    rel_ilastik_crop_dir: Path,
    ilastik_crop_shapes: Dict[str, Tuple[int, ...]],
):
    infos_group = input_data_group.get("infos")
    if infos_group is not None:
        for lane_group in infos_group.values():
            raw_data_group = lane_group.get("Raw Data")
            if raw_data_group is not None:
                ilastik_crop_file = _get_hdf5_file(
                    raw_data_group["filePath"][()].decode("ascii")
                )
                dataset_id = raw_data_group["datasetId"][()].decode("ascii")
                raw_data_group.clear()
                _init_project_raw_data_group(
                    raw_data_group,
                    dataset_id,
                    str(
                        rel_ilastik_crop_dir
                        / ilastik_crop_file.name
                        / _crop_dataset_path
                    ),
                    ilastik_crop_file.stem,
                    ilastik_crop_shapes[ilastik_crop_file.stem],
                )
    local_data_group = input_data_group.get("local_data")
    if local_data_group is not None:
        local_data_group.clear()


def _fix_project_pixel_classification_inplace(
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
                block_slice = block_dataset.attrs["blockSlice"].decode("ascii")
                block_slice = block_slice[1:-1].split(",")
                block_slice = [block_slice[i] for i in transpose_axes[:3]]
                block_slice = f"[{','.join(block_slice)}]"
                del labels_group[block_dataset_name]
                block_dataset = labels_group.create_dataset(
                    block_dataset_name, data=block
                )
                block_dataset.attrs["blockSlice"] = block_slice.encode("ascii")


def _fix_project_prediction_export_inplace(
    prediction_export_group: h5py.Group, rel_ilastik_probab_dir: Path
):
    prediction_export_group.clear()
    _logger.warning(
        "When exporting data from the graphical user interface of Ilastik, "
        "please manually edit the export image settings and enable "
        "renormalizing [min, max] from [0.0, 1.0] to [0, 65535]"
    )
    # prediction_export_group.create_dataset(
    #     "InputMin",
    #     data=np.array([0.0], dtype=np.float32),
    # )
    # prediction_export_group.create_dataset(
    #     "InputMax",
    #     data=np.array([1.0], dtype=np.float32),
    # )
    prediction_export_group.create_dataset(
        "ExportMin", data=np.array([0], dtype=np.uint16)
    )
    prediction_export_group.create_dataset(
        "ExportMax", data=np.array([65535], dtype=np.uint16)
    )
    prediction_export_group.create_dataset(
        "ExportDtype",
        dtype=h5py.string_dtype("utf-8"),
        data="uint16".encode("utf-8"),
    )
    prediction_export_group.create_dataset(
        "OutputAxisOrder",
        dtype=h5py.string_dtype("ascii"),
        data="yxc".encode("ascii"),
    )
    prediction_export_group.create_dataset(
        "OutputFormat",
        dtype=h5py.string_dtype("ascii"),
        data="tiff".encode("ascii"),
    )
    prediction_export_group.create_dataset(
        "OutputFilenameFormat",
        dtype=h5py.string_dtype("ascii"),
        data=f"{rel_ilastik_probab_dir}/{{nickname}}.tiff".encode("ascii"),
    )
    prediction_export_group.create_dataset(
        "OutputInternalPath",
        dtype=h5py.string_dtype("ascii"),
        data="exported_data".encode("ascii"),
    )
    prediction_export_group.create_dataset(
        "StorageVersion",
        dtype=h5py.string_dtype("utf-8"),
        data="0.1".encode("utf-8"),
    )


def _init_project_raw_data_group(
    raw_data_group: h5py.Group,
    dataset_id: str,
    file_path: str,
    nickname: str,
    shape: Tuple[int, ...],
):
    raw_data_group.create_dataset(
        "__class__",
        dtype=h5py.string_dtype("ascii"),
        data="RelativeFilesystemDatasetInfo".encode("ascii"),
    )
    raw_data_group.create_dataset("allowLabels", data=True)
    raw_data_group.create_dataset(
        "axistags",
        dtype=h5py.string_dtype("ascii"),
        data=_dataset_axistags.encode("ascii"),
    )
    raw_data_group.create_dataset(
        "datasetId",
        dtype=h5py.string_dtype("ascii"),
        data=dataset_id.encode("ascii"),
    )
    raw_data_group.create_dataset(
        "display_mode",
        dtype=h5py.string_dtype("ascii"),
        data=_dataset_display_mode.encode("ascii"),
    )
    raw_data_group.create_dataset(
        "filePath",
        dtype=h5py.string_dtype("ascii"),
        data=file_path.encode("ascii"),
    )
    raw_data_group.create_dataset(
        "location",
        dtype=h5py.string_dtype("ascii"),
        data="FileSystem".encode("ascii"),
    )
    raw_data_group.create_dataset(
        "nickname",
        dtype=h5py.string_dtype("ascii"),
        data=nickname.encode("ascii"),
    )
    raw_data_group.create_dataset("normalizeDisplay", data=False)
    raw_data_group.create_dataset(
        "shape", data=np.array(shape, dtype=np.int64)
    )


def _get_hdf5_file(hdf5_path: Union[str, PathLike]) -> Optional[Path]:
    hdf5_file = hdf5_path
    while hdf5_file is not None and Path(hdf5_file).suffix != ".h5":
        hdf5_file = Path(hdf5_file).parent
    return hdf5_file
