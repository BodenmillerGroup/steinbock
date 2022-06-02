import logging
import os
import re
from os import PathLike
from pathlib import Path
from typing import List, Optional, Sequence, Union

import numpy as np
import pandas as pd
import tifffile

from ._steinbock import SteinbockException

logger = logging.getLogger(__name__)
img_dtype = np.dtype(os.environ.get("STEINBOCK_IMG_DTYPE", "float32"))
mask_dtype = np.dtype(os.environ.get("STEINBOCK_MASK_DTYPE", "uint16"))


class SteinbockIOException(SteinbockException):
    pass


def _as_path_with_suffix(path: Union[str, PathLike], suffix: str) -> Path:
    path = Path(path)
    if re.fullmatch(r".+\.ome\.[^.]+", path.name, flags=re.IGNORECASE):
        stem, ome_suffix, suffix = path.name.rpartition(".ome.")
        if ome_suffix:
            path = path.with_name(f"{stem}.{suffix}")
        stem, ome_suffix, suffix = path.name.rpartition(".OME.")
        if ome_suffix:
            path = path.with_name(f"{stem}.{suffix}")
    return path.with_suffix(suffix)


def _to_dtype(src: np.ndarray, dst_dtype: np.dtype) -> np.ndarray:
    if src.dtype == dst_dtype:
        return src
    src_is_int = np.issubdtype(src.dtype, np.integer)
    dst_is_int = np.issubdtype(dst_dtype, np.integer)
    if not src_is_int and dst_is_int:
        src = np.around(src)
    if src_is_int:
        src_info = np.iinfo(src.dtype)
    else:
        src_info = np.finfo(src.dtype)
    if dst_is_int:
        dst_info = np.iinfo(dst_dtype)
    else:
        dst_info = np.finfo(dst_dtype)
    if src_info.min < dst_info.min or src_info.max > dst_info.max:
        src = np.clip(src, dst_info.min, dst_info.max)
    return src.astype(dst_dtype)


def _list_related_files(
    base_files: Sequence[Union[str, PathLike]],
    related_dir: Union[str, PathLike],
    related_suffix: str,
) -> List[Path]:
    related_files = []
    for base_file in base_files:
        related_file = _as_path_with_suffix(
            Path(related_dir) / Path(base_file).name, related_suffix
        )
        if not related_file.exists():
            raise SteinbockIOException() from FileNotFoundError(related_file)
        related_files.append(related_file)
    return related_files


def read_panel(
    panel_file: Union[str, PathLike], unfiltered: bool = False
) -> pd.DataFrame:
    panel = pd.read_csv(
        panel_file,
        sep=",|;",
        dtype={
            "channel": pd.StringDtype(),
            "name": pd.StringDtype(),
            "keep": pd.BooleanDtype(),
        },
        engine="python",
        true_values=["1"],
        false_values=["0"],
    )
    for required_col in ("channel", "name"):
        if required_col not in panel:
            raise SteinbockIOException(
                f"Missing '{required_col}' column in {panel_file}"
            )
    for notnan_col in ("channel", "keep"):
        if notnan_col in panel and panel[notnan_col].isna().any():
            raise SteinbockIOException(
                f"Missing values for '{notnan_col}' in {panel_file}"
            )
    for unique_col in ("channel", "name"):
        if unique_col in panel:
            if panel[unique_col].dropna().duplicated().any():
                raise SteinbockIOException(
                    f"Duplicated values for '{unique_col}' in {panel_file}"
                )
    if not unfiltered and "keep" in panel:
        panel = panel.loc[panel["keep"].astype(bool), :]
    return panel


def write_panel(panel: pd.DataFrame, panel_file: Union[str, PathLike]) -> None:
    panel = panel.copy()
    for col in panel.columns:
        if panel[col].convert_dtypes().dtype == pd.BooleanDtype():
            panel[col] = panel[col].astype(pd.UInt8Dtype())
    panel.to_csv(panel_file, index=False)


def list_image_files(
    img_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, img_dir, ".tiff")
    return sorted(Path(img_dir).rglob("*.tiff"))


def _fix_image_shape(img_file: Union[str, PathLike], img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    elif img.ndim == 5:
        size_t, size_z, size_c, size_y, size_x = img.shape
        if size_t != 1 or size_z != 1:
            raise SteinbockIOException(
                f"{img_file}: unsupported TZCYX shape {img.shape}"
            )
        img = img[0, 0, :, :, :]
    elif img.ndim == 6:
        size_t, size_z, size_c, size_y, size_x, size_s = img.shape
        if size_t != 1 or size_z != 1 or size_s != 1:
            raise SteinbockIOException(
                f"{img_file}: unsupported TZCYXS shape {img.shape}"
            )
        img = img[0, 0, :, :, :, 0]
    elif img.ndim != 3:
        raise SteinbockIOException(
            f"{img_file}: unsupported number of dimensions ({img.ndim})"
        )
    return img


def read_image(
    img_file: Union[str, PathLike],
    native_dtype: bool = False,
) -> np.ndarray:
    img = tifffile.imread(img_file, squeeze=False)
    img = _fix_image_shape(img_file, img)
    if not native_dtype:
        img = _to_dtype(img, img_dtype)
    return img


def mmap_image(img_file: Union[str, PathLike], mode="r", **kwargs) -> np.ndarray:
    if "imagej" not in kwargs and mode == "r+":
        kwargs["imagej"] = True
    img_exists = Path(img_file).exists()
    img = tifffile.memmap(img_file, mode=mode, **kwargs)
    if img_exists:
        if img.dtype != img_dtype:
            logger.warning(
                "Data type of memory-mapped image file %s (%s) is not %s",
                img_file,
                img.dtype,
                img_dtype,
            )
        img = _fix_image_shape(img_file, img)
    return img


def write_image(
    img: np.ndarray,
    img_file: Union[str, PathLike],
    ignore_dtype: bool = False,
) -> None:
    if not ignore_dtype:
        img = _to_dtype(img, img_dtype)
    tifffile.imwrite(
        img_file,
        data=img[np.newaxis, np.newaxis, :, :, :, np.newaxis],
        imagej=True,
    )


def read_image_info(image_info_file: Union[str, PathLike]) -> pd.DataFrame:
    image_info = pd.read_csv(
        image_info_file,
        sep=",|;",
        dtype={
            "image": pd.StringDtype(),
            "width_px": pd.UInt16Dtype(),
            "height_px": pd.UInt16Dtype(),
            "num_channels": pd.UInt8Dtype(),
        },
        engine="python",
    )
    for required_col in ("image", "width_px", "height_px", "num_channels"):
        if required_col not in image_info:
            raise SteinbockIOException(
                f"Missing '{required_col}' column in {image_info_file}"
            )
    for notnan_col in ("image", "width_px", "height_px", "num_channels"):
        if notnan_col in image_info and image_info[notnan_col].isna().any():
            raise SteinbockIOException(
                f"Missing values for '{notnan_col}' in {image_info_file}"
            )
    for unique_col in ("image",):
        if unique_col in image_info:
            if image_info[unique_col].dropna().duplicated().any():
                raise SteinbockIOException(
                    f"Duplicated values for '{unique_col}'" f" in {image_info_file}"
                )
    return image_info


def write_image_info(
    image_info: pd.DataFrame, image_info_file: Union[str, PathLike]
) -> None:
    image_info.to_csv(image_info_file, index=False)


def list_mask_files(
    mask_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, mask_dir, ".tiff")
    return sorted(Path(mask_dir).rglob("*.tiff"))


def _fix_mask_shape(mask_file: Union[str, PathLike], mask: np.ndarray) -> np.ndarray:
    if mask.ndim == 5:
        size_t, size_z, size_c, size_y, size_x = mask.shape
        if size_t != 1 or size_z != 1 or size_c != 1:
            raise SteinbockIOException(
                f"{mask_file}: unsupported TZCYX shape {mask.shape}"
            )
        mask = mask[0, 0, 0, :, :]
    elif mask.ndim == 6:
        size_t, size_z, size_c, size_y, size_x, size_s = mask.shape
        if size_t != 1 or size_z != 1 or size_c != 1 or size_s != 1:
            raise SteinbockIOException(
                f"{mask_file}: unsupported TZCYXS shape {mask.shape}"
            )
        mask = mask[0, 0, 0, :, :, 0]
    elif mask.ndim != 2:
        raise SteinbockIOException(
            f"{mask_file}: unsupported number of dimensions ({mask.ndim})"
        )
    return mask


def read_mask(
    mask_file: Union[str, PathLike],
    native_dtype: bool = False,
) -> np.ndarray:
    mask = tifffile.imread(mask_file, squeeze=False)
    mask = _fix_mask_shape(mask_file, mask)
    if not native_dtype:
        mask = _to_dtype(mask, mask_dtype)
    return mask


def mmap_mask(mask_file: Union[str, PathLike], mode="r", **kwargs) -> np.ndarray:
    if "imagej" not in kwargs and mode == "r+":
        kwargs["imagej"] = True
    mask_exists = Path(mask_file).exists()
    mask = tifffile.memmap(mask_file, mode=mode, **kwargs)
    if mask_exists:
        if mask.dtype != mask_dtype:
            logger.warning(
                "Data type of memory-mapped mask file %s (%s) is not %s",
                mask_file,
                mask.dtype,
                mask_dtype,
            )
        mask = _fix_mask_shape(mask_file, mask)
    return mask


def write_mask(
    mask: np.ndarray,
    mask_file: Union[str, PathLike],
    ignore_dtype: bool = False,
) -> None:
    if not ignore_dtype:
        mask = _to_dtype(mask, mask_dtype)
    tifffile.imwrite(
        mask_file,
        data=mask[np.newaxis, np.newaxis, np.newaxis, :, :, np.newaxis],
        imagej=True,
    )


def list_data_files(
    data_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, data_dir, ".csv")
    return sorted(Path(data_dir).rglob("*.csv"))


def read_data(data_file: Union[str, PathLike]) -> pd.DataFrame:
    return pd.read_csv(data_file, sep=",|;", index_col="Object", engine="python")


def write_data(data: pd.DataFrame, data_file: Union[str, PathLike]) -> None:
    data = data.reset_index()
    data.to_csv(data_file, index=False)


def list_neighbors_files(
    neighbors_dir: Union[str, PathLike],
    base_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> List[Path]:
    if base_files is not None:
        return _list_related_files(base_files, neighbors_dir, ".csv")
    return sorted(Path(neighbors_dir).rglob("*.csv"))


def read_neighbors(neighbors_file: Union[str, PathLike]) -> pd.DataFrame:
    return pd.read_csv(
        neighbors_file,
        sep=",|;",
        usecols=["Object", "Neighbor", "Distance"],
        dtype={
            "Object": mask_dtype,
            "Neighbor": mask_dtype,
            "Distance": np.float32,
        },
        engine="python",
    )


def write_neighbors(
    neighbors: pd.DataFrame, neighbors_file: Union[str, PathLike]
) -> None:
    neighbors = neighbors.loc[:, ["Object", "Neighbor", "Distance"]].astype(
        {
            "Object": mask_dtype,
            "Neighbor": mask_dtype,
            "Distance": np.float32,
        }
    )
    neighbors.to_csv(neighbors_file, index=False)
