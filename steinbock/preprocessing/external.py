import logging
from os import PathLike
from pathlib import Path
from typing import Generator, List, Sequence, Tuple, Union

import imageio
import numpy as np
import pandas as pd

from .. import io
from ._preprocessing import SteinbockPreprocessingException

logger = logging.getLogger(__name__)


class SteinbockExternalPreprocessingException(SteinbockPreprocessingException):
    pass


def _read_external_image(ext_img_file: Union[str, PathLike]) -> np.ndarray:
    # try tifffile-based reading first, for memory reasons
    try:
        return io.read_image(ext_img_file, native_dtype=True)
    except:
        pass  # skipped intentionally
    ext_img = imageio.volread(ext_img_file)
    orig_img_shape = ext_img.shape
    while ext_img.ndim > 3 and ext_img.shape[0] == 1:
        ext_img = np.squeeze(ext_img, axis=0)
    while ext_img.ndim > 3 and ext_img.shape[-1] == 1:
        ext_img = np.squeeze(ext_img, axis=-1)
    if ext_img.ndim == 2:
        ext_img = ext_img[np.newaxis, :, :]
    elif ext_img.ndim != 3:
        raise SteinbockExternalPreprocessingException(
            f"Unsupported shape {orig_img_shape} for image {ext_img_file}"
        )
    return ext_img


def list_image_files(ext_img_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(ext_img_dir).rglob("*.*"))


def create_panel_from_image_files(
    ext_img_files: Sequence[Union[str, PathLike]]
) -> pd.DataFrame:
    num_channels = None
    for ext_img_file in ext_img_files:
        try:
            ext_img = _read_external_image(ext_img_file)
            num_channels = ext_img.shape[0]
            break
        except:
            pass  # skipped intentionally
    if num_channels is None:
        raise SteinbockExternalPreprocessingException("No valid images found")
    panel = pd.DataFrame(
        data={
            "channel": range(1, num_channels + 1),
            "name": np.nan,
            "keep": True,
            "ilastik": range(1, num_channels + 1),
            "deepcell": np.nan,
        },
    )
    panel["channel"] = panel["channel"].astype(pd.StringDtype())
    panel["name"] = panel["name"].astype(pd.StringDtype())
    panel["keep"] = panel["keep"].astype(pd.BooleanDtype())
    panel["ilastik"] = panel["ilastik"].astype(pd.UInt8Dtype())
    panel["deepcell"] = panel["deepcell"].astype(pd.UInt8Dtype())
    return panel


def try_preprocess_images_from_disk(
    ext_img_files: Sequence[Union[str, PathLike]]
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for ext_img_file in ext_img_files:
        try:
            img = _read_external_image(ext_img_file)
        except:
            logger.warning(f"Unsupported file format: {ext_img_file}")
            continue
        yield ext_img_file, img
        del img
