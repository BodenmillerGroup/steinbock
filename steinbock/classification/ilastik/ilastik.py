import h5py
import json
import logging
import numpy as np

import shutil
import subprocess

from enum import IntEnum
from os import PathLike
from pathlib import Path
from typing import Dict, Generator, List, Optional, Sequence, Tuple, Union
from uuid import uuid1

from steinbock import io, utils


class VigraAxisInfo(IntEnum):
    Channels = 1
    Space = 2
    Angle = 4
    Time = 8
    Frequency = 16
    Edge = 32
    UnknownAxisType = 64


img_dataset_path = "img"
crop_dataset_path = "crop"
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
_project_file_template = _data_dir / "pixel_classifier.ilp"


def list_images(img_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(img_dir).rglob("*.h5"))


def list_crops(crop_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(crop_dir).rglob("*.h5"))


def create_images(
    src_img_files: Sequence[Union[str, PathLike]],
    channel_groups: Optional[np.ndarray] = None,
    prepend_mean: bool = True,
    img_scale: int = 1,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for src_img_file in src_img_files:
        src_img_file = Path(src_img_file)
        img = io.read_image(src_img_file)
        if channel_groups is not None:
            img = np.stack(
                [
                    np.mean(img[channel_groups == channel_group, :, :], axis=0)
                    for channel_group in np.unique(
                        channel_groups[~np.isnan(channel_groups)]
                    )
                ],
            )
        if prepend_mean:
            mean_img = img.mean(axis=0, keepdims=True)
            img = np.concatenate((mean_img, img))
        if img_scale > 1:
            img = img.repeat(img_scale, axis=1)
            img = img.repeat(img_scale, axis=2)
        yield src_img_file, img
        del img


def create_crops(
    img_files: Sequence[Union[str, PathLike]],
    crop_size: int,
    seed=None,
) -> Generator[
    Tuple[Path, Optional[int], Optional[int], Optional[np.ndarray]], None, None
]:
    rng = np.random.default_rng(seed=seed)
    for img_file in img_files:
        img_file = Path(img_file)
        img = read_image(img_file, img_dataset_path)
        yx_shape = img.shape[1:]
        if all(shape >= crop_size for shape in yx_shape):
            x_start = rng.integers(img.shape[2] - crop_size)
            x_end = x_start + crop_size
            y_start = rng.integers(img.shape[1] - crop_size)
            y_end = y_start + crop_size
            crop = img[:, y_start:y_end, x_start:x_end]
            yield img_file, x_start, y_start, crop
            del crop
        else:
            yield img_file, None, None, None


def create_project(
    crop_files: Sequence[Union[str, PathLike]],
    project_file: Union[str, PathLike],
):
    project_file = Path(project_file)
    shutil.copyfile(_project_file_template, project_file)
    dataset_id = str(uuid1())
    with h5py.File(project_file, mode="a") as f:
        infos = f["Input Data/infos"]
        for i, crop_file in enumerate(crop_files):
            crop_file = Path(crop_file)
            rel_crop_file = crop_file.relative_to(project_file.parent)
            with h5py.File(crop_file, mode="r") as f_crop:
                crop_shape = f_crop[crop_dataset_path].shape
            lane = infos.create_group(f"lane{i:04d}")
            lane.create_group("Prediction Mask")
            _init_project_raw_data_group(
                lane.create_group("Raw Data"),
                dataset_id,
                str(rel_crop_file / crop_dataset_path),
                crop_file.stem,
                crop_shape,
            )


def classify_pixels(
    ilastik_binary: Union[str, PathLike],
    project_file: Union[str, PathLike],
    img_files: Sequence[Union[str, PathLike]],
    probabilities_dir: Union[str, PathLike],
    num_threads: Optional[int] = None,
    memory_limit: Optional[int] = None,
    ilastik_env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    probabilities_dir = Path(probabilities_dir)
    args = [
        str(ilastik_binary),
        "--headless",
        f"--project={project_file}",
        "--readonly",
        "--input_axes=cyx",
        "--export_source=Probabilities",
        "--output_format=tiff",
        f"--output_filename_format={probabilities_dir}/{{nickname}}.tiff",
        "--export_dtype=uint16",
        "--output_axis_order=yxc",
        "--pipeline_result_drange=(0.0,1.0)",
        "--export_drange=(0,65535)",
    ]
    for img_file in img_files:
        args.append(str(Path(img_file) / img_dataset_path))
    env = None
    if ilastik_env is not None:
        env = ilastik_env.copy()
        if num_threads is not None:
            env["LAZYFLOW_THREADS"] = num_threads
        if memory_limit is not None:
            env["LAZYFLOW_TOTAL_RAM_MB"] = memory_limit
    result = utils.run_captured(args, env=env)
    probabilities_files = probabilities_dir.rglob(f"*-{img_dataset_path}.tiff")
    for probabilities_file in sorted(probabilities_files):
        probabilities_file.rename(
            probabilities_file.with_name(
                probabilities_file.name.replace(f"-{img_dataset_path}", ""),
            ),
        )
    return result


def fix_crops_inplace(
    crop_files: Sequence[Union[str, PathLike]],
    axis_order: Optional[str] = None,
) -> Generator[Tuple[Path, Tuple[int, ...], np.ndarray], None, None]:
    for crop_file in crop_files:
        with h5py.File(crop_file, mode="r") as f:
            crop_dataset = None
            if crop_dataset_path in f:
                crop_dataset = f[crop_dataset_path]
            elif crop_file.stem in f:
                crop_dataset = f[crop_file.stem]
            elif len(f) == 1:
                crop_dataset = next(iter(f.values()))
            else:
                raise ValueError(f"Unknown dataset name: {crop_file}")
            if crop_dataset.attrs.get("steinbock", False):
                continue
            crop = crop_dataset[()]
            orig_axis_order = None
            if axis_order is not None:
                orig_axis_order = list(axis_order)
            elif "axistags" in crop_dataset.attrs:
                axis_tags = json.loads(crop_dataset.attrs["axistags"])
                orig_axis_order = [item["key"] for item in axis_tags["axes"]]
            else:
                raise ValueError(f"Unknown axis order: {crop_file}")
        if len(orig_axis_order) != crop.ndim:
            raise ValueError(f"Incompatible axis order: {crop_file}")
        channel_axis_index = orig_axis_order.index("c")
        size_x = crop.shape[orig_axis_order.index("x")]
        size_y = crop.shape[orig_axis_order.index("y")]
        num_channels = crop.size // (size_x * size_y)
        if crop.shape[channel_axis_index] != num_channels:
            channel_axis_indices = (
                i
                for i, a in enumerate(orig_axis_order)
                if a not in ("x", "y") and crop.shape[i] == num_channels
            )
            channel_axis_index = next(channel_axis_indices, None)
        if channel_axis_index is None:
            raise ValueError(f"Unknown channel axis: {crop_file}")
        new_axis_order = orig_axis_order.copy()
        new_axis_order.insert(0, new_axis_order.pop(channel_axis_index))
        new_axis_order.insert(1, new_axis_order.pop(new_axis_order.index("y")))
        new_axis_order.insert(2, new_axis_order.pop(new_axis_order.index("x")))
        transpose_axes = [orig_axis_order.index(a) for a in new_axis_order]
        crop = np.transpose(crop, axes=transpose_axes)
        crop = np.reshape(crop, crop.shape[:3])
        crop = crop.astype(np.float32)
        yield crop_file, transpose_axes, crop
        del crop


def fix_project_inplace(
    project_file: Union[str, PathLike],
    crop_dir: Union[str, PathLike],
    probabilities_dir: Union[str, PathLike],
    crop_shapes: Dict[str, Tuple[int, ...]],
    transpose_axes: List[int],
):
    project_file = Path(project_file)
    crop_dir = Path(crop_dir)
    probabilities_dir = Path(probabilities_dir)
    rel_crop_dir = crop_dir.relative_to(project_file.parent)
    rel_probabilities_dir = probabilities_dir.relative_to(project_file.parent)
    with h5py.File(project_file, "a") as f:
        if "Input Data" in f:
            _fix_project_input_data_inplace(
                f["Input Data"],
                rel_crop_dir,
                crop_shapes,
            )
        if "PixelClassification" in f:
            _fix_project_pixel_classification_inplace(
                f["PixelClassification"],
                transpose_axes,
            )
        if "Prediction Export" in f:
            _fix_project_prediction_export_inplace(
                f["Prediction Export"],
                rel_probabilities_dir,
            )


def _fix_project_input_data_inplace(
    input_data_group: h5py.Group,
    rel_crop_dir: Path,
    crop_shapes: Dict[str, Tuple[int, ...]],
):
    infos_group = input_data_group.get("infos")
    if infos_group is not None:
        for lane_group in infos_group.values():
            raw_data_group = lane_group.get("Raw Data")
            if raw_data_group is not None:
                crop_file = _get_hdf5_file(
                    raw_data_group["filePath"][()].decode("ascii"),
                )
                dataset_id = raw_data_group["datasetId"][()].decode("ascii")
                raw_data_group.clear()
                _init_project_raw_data_group(
                    raw_data_group,
                    dataset_id,
                    str(rel_crop_dir / crop_file.name / crop_dataset_path),
                    crop_file.stem,
                    crop_shapes[crop_file.stem],
                )
    local_data_group = input_data_group.get("local_data")
    if local_data_group is not None:
        local_data_group.clear()


def _fix_project_pixel_classification_inplace(
    pixel_classification_group: h5py.Group,
    transpose_axes: List[int],
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
                    block_dataset_name,
                    data=block,
                )
                block_dataset.attrs["blockSlice"] = block_slice.encode("ascii")


def _fix_project_prediction_export_inplace(
    prediction_export_group: h5py.Group,
    rel_probabilities_dir: Path,
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
        data=f"{rel_probabilities_dir}/{{nickname}}.tiff".encode("ascii"),
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


def _get_hdf5_file(path: Union[str, PathLike]) -> Optional[Path]:
    path = Path(path)
    while path is not None and path.suffix != ".h5":
        path = path.parent
    return path


def read_image(
    img_file: Union[str, PathLike],
    dataset_path: Union[str, PathLike],
) -> np.ndarray:
    img_file = Path(img_file).with_suffix(".h5")
    with h5py.File(img_file, mode="r") as f:
        return f[str(dataset_path)][()]


def write_image(
    img: np.ndarray,
    img_file: Union[str, PathLike],
    dataset_path: Union[str, PathLike],
) -> Path:
    img_file = Path(img_file).with_suffix(".h5")
    with h5py.File(img_file, mode="w") as f:
        dataset = f.create_dataset(str(dataset_path), data=img)
        dataset.attrs["display_mode"] = _steinbock_display_mode.encode("ascii")
        dataset.attrs["axistags"] = _steinbock_axis_tags.encode("ascii")
        dataset.attrs["steinbock"] = True
    return img_file


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
