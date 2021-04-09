import h5py
import json
import logging
import numpy as np

import os
import shutil
import subprocess

from enum import IntEnum
from os import PathLike
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union
from uuid import uuid1

from steinbock.utils import io, system


class VigraAxisInfo(IntEnum):
    Channels = 1
    Space = 2
    Angle = 4
    Time = 8
    Frequency = 16
    Edge = 32
    UnknownAxisType = 64


img_dataset_name = "img"
patch_dataset_name = "patch"
panel_ilastik_col = "ilastik"
logger = logging.getLogger(__name__)

_steinbock_display_mode = "grayscale"
_steinbock_axis_tags = json.dumps(
    {
        "axes": [
            {"key": "c", "typeFlags": VigraAxisInfo.Channels.value},
            {"key": "y", "typeFlags": VigraAxisInfo.Space.value},
            {"key": "x", "typeFlags": VigraAxisInfo.Space.value},
        ]
    }
)

_data_dir = Path(__file__).parent / "data"
_ilastik_project_file_template = _data_dir / "pixel_classifier.ilp"


def create_ilastik_images(
    img_files: Sequence[Union[str, PathLike]],
    ilastik_img_dir: Union[str, PathLike],
    channel_indices: Optional[Sequence[int]] = None,
    img_scale: int = 1,
) -> List[Path]:
    ilastik_img_files = []
    ilastik_img_dir = Path(ilastik_img_dir)
    for img_file in img_files:
        img_file = Path(img_file)
        ilastik_img = io.read_image(img_file)
        if channel_indices is not None:
            ilastik_img = ilastik_img[channel_indices, :, :]
        if img_scale > 1:
            ilastik_img = ilastik_img.repeat(img_scale, axis=1)
            ilastik_img = ilastik_img.repeat(img_scale, axis=2)
        ilastik_img_file = ilastik_img_dir / f"{img_file.stem}.h5"
        _write_hdf5_image(ilastik_img, ilastik_img_file, img_dataset_name)
        ilastik_img_files.append(ilastik_img_file)
    return ilastik_img_files


def create_ilastik_patches(
    ilastik_img_files: Sequence[Union[str, PathLike]],
    ilastik_patch_dir: Union[str, PathLike],
    patch_size: int,
    seed=None,
) -> List[Path]:
    ilastik_patch_files = []
    ilastik_patch_dir = Path(ilastik_patch_dir)
    rng = np.random.default_rng(seed=seed)
    for ilastik_img_file in ilastik_img_files:
        ilastik_img_file = Path(ilastik_img_file)
        ilastik_img = _read_hdf5_image(ilastik_img_file, img_dataset_name)
        yx_shape = ilastik_img.shape[1:]
        if all(shape >= patch_size for shape in yx_shape):
            x_start = rng.integers(ilastik_img.shape[2] - patch_size)
            x_end = x_start + patch_size
            y_start = rng.integers(ilastik_img.shape[1] - patch_size)
            y_end = y_start + patch_size
            ilastik_patch = ilastik_img[:, y_start:y_end, x_start:x_end]
            ilastik_patch_file = ilastik_patch_dir / (
                f"{ilastik_img_file.stem}_x{x_start}_y{y_start}"
                f"_w{patch_size}_h{patch_size}.h5"
            )
            _write_hdf5_image(
                ilastik_patch,
                ilastik_patch_file,
                patch_dataset_name,
            )
            ilastik_patch_files.append(ilastik_patch_file)
        else:
            logger.warn(f"Image too small for patch size: {ilastik_img_file}")
    return ilastik_patch_files


def create_ilastik_project(
    ilastik_patch_files: Sequence[Union[str, PathLike]],
    ilastik_project_file: Union[str, PathLike],
):
    ilastik_project_file = Path(ilastik_project_file)
    shutil.copyfile(_ilastik_project_file_template, ilastik_project_file)
    dataset_id = str(uuid1())
    with h5py.File(ilastik_project_file, mode="a") as f:
        infos = f["Input Data/infos"]
        for i, ilastik_patch_file in enumerate(ilastik_patch_files):
            ilastik_patch_file = Path(ilastik_patch_file)
            relative_ilastik_patch_file = ilastik_patch_file.relative_to(
                ilastik_project_file.parent
            )
            with h5py.File(ilastik_patch_file, mode="r") as f_patch:
                patch_shape = f_patch[patch_dataset_name].shape
            lane = infos.create_group(f"lane{i:04d}")
            lane.create_group("Prediction Mask")
            _init_raw_data_group(
                lane.create_group("Raw Data"),
                dataset_id,
                str(relative_ilastik_patch_file / patch_dataset_name),
                ilastik_patch_file.stem,
                patch_shape,
            )


def classify_pixels(
    ilastik_binary: Union[str, PathLike],
    ilastik_project_file: Union[str, PathLike],
    ilastik_img_files: Sequence[Union[str, PathLike]],
    ilastik_probab_dir: Union[str, PathLike],
    num_threads: Optional[int] = None,
    memory_limit: Optional[int] = None,
) -> subprocess.CompletedProcess:
    args = [
        ilastik_binary,
        "--headless",
        f"--project={ilastik_project_file}",
        "--readonly",
        "--input_axes=cyx",
        "--export_source=Probabilities",
        "--output_format=tiff",
        f"--output_filename_format={ilastik_probab_dir}/{{nickname}}.tiff",
        "--export_dtype=uint16",
        "--output_axis_order=yxc",
        "--pipeline_result_drange=(0.0,1.0)",
        "--export_drange=(0,65535)",
    ]
    for ilastik_img_file in ilastik_img_files:
        args.append(str(Path(ilastik_img_file) / img_dataset_name))
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    if num_threads is not None:
        env["LAZYFLOW_THREADS"] = num_threads
    if memory_limit is not None:
        env["LAZYFLOW_TOTAL_RAM_MB"] = memory_limit
    result = system.run_captured(args, env=env)
    for ilastik_probability_file in sorted(
        Path(ilastik_probab_dir).glob(f"*-{img_dataset_name}.tiff")
    ):
        n = ilastik_probability_file.name.replace(f"-{img_dataset_name}", "")
        ilastik_probability_file.rename(ilastik_probability_file.with_name(n))
    return result


def fix_patches_and_project_inplace(
    ilastik_project_file: Union[str, PathLike],
    ilastik_patch_dir: Union[str, PathLike],
    ilastik_probab_dir: Union[str, PathLike],
    axis_order: Optional[str] = None,
):
    patch_shapes, transpose_axes = _fix_patches_inplace(
        ilastik_patch_dir,
        axis_order,
    )
    _fix_project_inplace(
        ilastik_project_file,
        ilastik_patch_dir,
        ilastik_probab_dir,
        patch_shapes,
        transpose_axes,
    )


def _fix_patches_inplace(
    ilastik_patch_dir: Union[str, PathLike],
    axis_order: Optional[str],
) -> Tuple[Dict[str, Tuple[int, ...]], List[int]]:
    patch_shapes = {}
    transpose_axes = None
    ilastik_patch_files = sorted(Path(ilastik_patch_dir).glob("*.h5"))
    for ilastik_patch_file in ilastik_patch_files:
        ilastik_patch_file = Path(ilastik_patch_file)
        with h5py.File(ilastik_patch_file, mode="r") as f:
            patch_dataset = None
            if patch_dataset_name in f:
                patch_dataset = f[patch_dataset_name]
            elif ilastik_patch_file.stem in f:
                patch_dataset = f[ilastik_patch_file.stem]
            elif len(f) == 1:
                patch_dataset = next(iter(f.values()))
            else:
                raise ValueError(f"Unknown dataset name: {ilastik_patch_file}")
            patch = patch_dataset[()]
            orig_axis_order = None
            if axis_order is not None:
                orig_axis_order = list(axis_order)
            elif "axistags" in patch_dataset.attrs:
                axis_tags_str = patch_dataset.attrs["axistags"]
                axis_tags = json.loads(axis_tags_str)
                orig_axis_order = [item["key"] for item in axis_tags["axes"]]
            else:
                raise ValueError(f"Unknown axis order: {ilastik_patch_file}")
        if len(orig_axis_order) != patch.ndim:
            raise ValueError(f"Incompatible axis order: {ilastik_patch_file}")
        channel_axis_index = orig_axis_order.index("c")
        size_x = patch.shape[orig_axis_order.index("x")]
        size_y = patch.shape[orig_axis_order.index("y")]
        num_channels = patch.size // (size_x * size_y)
        if patch.shape[channel_axis_index] != num_channels:
            channel_axis_index = next(
                (
                    i
                    for i, a in enumerate(orig_axis_order)
                    if patch.shape[i] == num_channels and a not in ("x", "y")
                ),
                None,
            )
        if channel_axis_index is None:
            raise ValueError(f"Unknown channel axis: {ilastik_patch_file}")
        new_axis_order = orig_axis_order.copy()
        new_axis_order.insert(0, new_axis_order.pop(channel_axis_index))
        new_axis_order.insert(1, new_axis_order.pop(new_axis_order.index("y")))
        new_axis_order.insert(2, new_axis_order.pop(new_axis_order.index("x")))
        new_transpose_axes = [orig_axis_order.index(a) for a in new_axis_order]
        if transpose_axes is not None and new_transpose_axes != transpose_axes:
            raise ValueError("Inconsistenn axis orders across patches")
        transpose_axes = new_transpose_axes
        patch = np.transpose(patch, axes=transpose_axes)
        patch = np.reshape(patch, patch.shape[:3])
        patch = patch.astype(np.float32)
        _write_hdf5_image(patch, ilastik_patch_file, patch_dataset_name)
        patch_shapes[ilastik_patch_file.name] = patch.shape
    return patch_shapes, transpose_axes


def _fix_project_inplace(
    ilastik_project_file: Union[str, PathLike],
    ilastik_patch_dir: Union[str, PathLike],
    ilastik_probab_dir: Union[str, PathLike],
    patch_shapes: Dict[str, Tuple[int, ...]],
    transpose_axes: List[int],
):
    ilastik_project_file = Path(ilastik_project_file)
    ilastik_patch_dir = Path(ilastik_patch_dir)
    ilastik_probab_dir = Path(ilastik_probab_dir)
    relative_ilastik_patch_dir = ilastik_patch_dir.relative_to(
        ilastik_project_file.parent
    )
    relative_ilastik_probab_dir = ilastik_probab_dir.relative_to(
        ilastik_project_file.parent
    )
    with h5py.File(ilastik_project_file, "a") as f:
        if "Input Data" in f:
            _fix_project_input_data_inplace(
                f["Input Data"],
                relative_ilastik_patch_dir,
                patch_shapes,
            )
        if "PixelClassification" in f:
            _fix_project_pixel_classification_inplace(
                f["PixelClassification"],
                transpose_axes,
            )
        if "Prediction Export" in f:
            _fix_project_prediction_export_inplace(
                f["Prediction Export"],
                relative_ilastik_probab_dir,
            )


def _fix_project_input_data_inplace(
    input_data_group: h5py.Group,
    relative_ilastik_patch_dir: Path,
    patch_shapes: Dict[str, Tuple[int, ...]],
):
    infos_group = input_data_group.get("infos")
    if infos_group is not None:
        for lane_group in infos_group.values():
            raw_data_group = lane_group.get("Raw Data")
            if raw_data_group is not None:
                ilastik_patch_file = _get_hdf5_file(
                    raw_data_group["filePath"][()].decode("ascii")
                )
                dataset_id = raw_data_group["datasetId"][()].decode("ascii")
                file_path = str(
                    relative_ilastik_patch_dir
                    / ilastik_patch_file.name
                    / patch_dataset_name
                )
                raw_data_group.clear()
                _init_raw_data_group(
                    raw_data_group,
                    dataset_id,
                    file_path,
                    ilastik_patch_file.stem,
                    patch_shapes[ilastik_patch_file.name],
                )
    local_data_group = input_data_group.get("local_data")
    if local_data_group is not None:
        local_data_group.clear()


def _fix_project_pixel_classification_inplace(
    pixel_classification_group: h5py.Group,
    transpose_axes: List[int],
):
    label_names_dataset = pixel_classification_group.get("LabelNames")
    if label_names_dataset is not None:
        if len(label_names_dataset) != 3:
            raise ValueError("Unsupported number of labels")
        label_names_dataset[0] = "Nucleus".encode("ascii")
        label_names_dataset[1] = "Cytoplasm".encode("ascii")
        label_names_dataset[2] = "Background".encode("ascii")
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
                    block_dataset_name,
                    data=block,
                )
                block_dataset.attrs["blockSlice"] = block_slice.encode("ascii")


def _fix_project_prediction_export_inplace(
    prediction_export_group: h5py.Group,
    relative_ilastik_probab_dir: Path,
):
    prediction_export_group.clear()
    logger.warn(
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
        "ExportMin",
        data=np.array([0], dtype=np.uint16),
    )
    prediction_export_group.create_dataset(
        "ExportMax",
        data=np.array([65535], dtype=np.uint16),
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
        data=f"{relative_ilastik_probab_dir}/{{nickname}}.tiff".encode(
            "ascii",
        ),
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


def _read_hdf5_image(
    path: Union[str, PathLike],
    dataset_name: str,
) -> np.ndarray:
    with h5py.File(path, mode="r") as f:
        return f[dataset_name][()]


def _write_hdf5_image(
    img: np.ndarray,
    path: Union[str, PathLike],
    dataset_name: str,
):
    with h5py.File(path, mode="w") as f:
        dataset = f.create_dataset(dataset_name, data=img)
        dataset.attrs["display_mode"] = _steinbock_display_mode.encode("ascii")
        dataset.attrs["axistags"] = _steinbock_axis_tags.encode("ascii")


def _get_hdf5_file(path: Union[str, PathLike]) -> Optional[Path]:
    path = Path(path)
    while path is not None and path.suffix != ".h5":
        path = path.parent
    return path


def _init_raw_data_group(
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
    raw_data_group.create_dataset(
        "allowLabels",
        data=True,
    )
    raw_data_group.create_dataset(
        "axistags",
        dtype=h5py.string_dtype("ascii"),
        data=_steinbock_axis_tags.encode("ascii"),
    )
    raw_data_group.create_dataset(
        "datasetId",
        dtype=h5py.string_dtype("ascii"),
        data=dataset_id.encode("ascii"),
    )
    raw_data_group.create_dataset(
        "display_mode",
        dtype=h5py.string_dtype("ascii"),
        data=_steinbock_display_mode.encode("ascii"),
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
    raw_data_group.create_dataset(
        "normalizeDisplay",
        data=False,
    )
    raw_data_group.create_dataset(
        "shape",
        data=np.array(shape, dtype=np.int64),
    )
