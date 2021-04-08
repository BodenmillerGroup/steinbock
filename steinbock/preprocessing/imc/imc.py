import logging
import numpy as np

from imctools.io.mcd.mcdparser import McdParser
from imctools.io.txt.txtparser import TxtParser
from os import PathLike
from pathlib import Path
from scipy.ndimage import maximum_filter
from typing import Generator, Optional, Sequence, Tuple, Union


logger = logging.getLogger(__name__)


def preprocess_images(
    mcd_files: Sequence[Union[str, PathLike]],
    txt_files: Sequence[Union[str, PathLike]],
    img_dir: Union[str, PathLike],
    channel_indices: Optional[Sequence[int]] = None,
    hpf: Optional[float] = None,
) -> Generator[Tuple[Path, Optional[int], np.ndarray], None, None]:
    remaining_txt_files = list(txt_files)
    for mcd_file in mcd_files:
        mcd_file = Path(mcd_file)
        with McdParser(mcd_file) as mcd_parser:
            for acquisition in mcd_parser.session.acquisitions.values():
                txt_file = None
                filtered_txt_files = [
                    txt_file
                    for txt_file in txt_files
                    if Path(txt_file).stem.startswith(mcd_file.stem)
                    and Path(txt_file).stem.endswith(f"_{acquisition.id}")
                ]
                if len(filtered_txt_files) == 1:
                    remaining_txt_files.remove(filtered_txt_files[0])
                    txt_file = Path(filtered_txt_files[0])
                data = mcd_parser.get_acquisition_data(acquisition.id)
                if data.image_data is None or not data.is_valid:
                    logger.warning(f"File corrupted: {mcd_file.name}")
                    if txt_file is not None:
                        logger.info(f"Restoring from {txt_file.name}")
                        with TxtParser(
                            txt_file, slide_id=acquisition.slide_id
                        ) as txt_parser:
                            data = txt_parser.get_acquisition_data()
                if data.image_data is not None and data.is_valid:
                    img = preprocess_image(
                        data.image_data,
                        channel_indices,
                        hpf=hpf,
                    )
                    yield mcd_file, acquisition.id, img
    while len(remaining_txt_files) > 0:
        txt_file = Path(remaining_txt_files.pop(0))
        with TxtParser(txt_file) as txt_parser:
            data = txt_parser.get_acquisition_data()
        if data.is_valid:
            img = preprocess_image(data.image_data, channel_indices, hpf=hpf)
            yield txt_file, None, img


def preprocess_image(
    img: np.ndarray,
    channel_indices: Optional[Sequence[int]] = None,
    hpf: Optional[float] = None,
) -> np.ndarray:
    if channel_indices is not None:
        img = img[channel_indices, :, :]
    img = img.astype(np.float32)
    if hpf is not None:
        img = filter_hot_pixels(img, hpf)
    return img


def filter_hot_pixels(img: np.ndarray, thres: float) -> np.ndarray:
    kernel = np.ones((1, 3, 3), dtype=np.uint8)
    kernel[0, 1, 1] = 0
    max_neighbor_img = maximum_filter(img, footprint=kernel, mode="mirror")
    return np.where(img - max_neighbor_img > thres, max_neighbor_img, img)
