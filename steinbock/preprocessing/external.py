import logging
import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from typing import Generator, List, Optional, Sequence, Tuple, Union

from steinbock import io


_logger = logging.getLogger(__name__)


def list_image_files(ext_img_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(ext_img_dir).rglob("*.*"))


def create_panel_from_image_files(
    ext_img_files: Sequence[Union[str, PathLike]]
) -> pd.DataFrame:
    num_channels = None
    for ext_img_file in ext_img_files:
        try:
            ext_img = io.read_image(
                ext_img_file,
                keep_suffix=True,
                use_imageio=True,
                native_dtype=True,
            )
            if ext_img is not None:
                num_channels = ext_img.shape[0]
                break
        except:
            pass
    if num_channels is None:
        raise IOError("No valid images found")
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
    ext_img_files: Sequence[Union[str, PathLike]],
    channel_indices: Optional[Sequence[int]] = None,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    for ext_img_file in ext_img_files:
        try:
            ext_img = io.read_image(
                ext_img_file,
                keep_suffix=True,
                use_imageio=True,
                native_dtype=True,
            )
            if ext_img is None:
                _logger.warning(
                    f"Unsupported image data in file {ext_img_file}"
                )
                continue
            if channel_indices is not None:
                if max(channel_indices) > ext_img.shape[0]:
                    _logger.warning(
                        f"Channel indices out of bounds for file "
                        f"{ext_img_file} with {ext_img.shape[0]} channels"
                    )
                ext_img = ext_img[channel_indices, :, :]
            yield ext_img_file, ext_img
            del ext_img
        except:
            _logger.exception(f"Error reading file {ext_img_file}")
