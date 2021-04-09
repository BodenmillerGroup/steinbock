import logging
import numpy as np
import pandas as pd

from imctools.io.mcd.mcdparser import McdParser
from imctools.io.txt.txtparser import TxtParser
from os import PathLike
from pathlib import Path
from scipy.ndimage import maximum_filter
from typing import Generator, Optional, Sequence, Tuple, Union

from steinbock.classification.ilastik.ilastik import panel_ilastik_col
from steinbock.utils import io


logger = logging.getLogger(__name__)

imc_panel_metal_col = "Metal Tag"
imc_panel_name_col = "Target"
imc_panel_enable_col = "full"
imc_panel_ilastik_col = "ilastik"


def preprocess_panel(
    imc_panel_file: Union[str, Path],
) -> Tuple[pd.DataFrame, Sequence[str]]:
    imc_panel = pd.read_csv(imc_panel_file)
    if imc_panel_metal_col not in imc_panel:
        raise ValueError(f"Missing {imc_panel_metal_col} column in IMC panel")
    if imc_panel_name_col not in imc_panel:
        raise ValueError(f"Missing {imc_panel_name_col} column in IMC panel")
    panel = pd.DataFrame(
        data={
            io.panel_number_col: imc_panel.index.values + 1,
            io.panel_name_col: imc_panel[imc_panel_name_col].tolist(),
            io.panel_enable_col: imc_panel[imc_panel_enable_col].tolist(),
            panel_ilastik_col: imc_panel[imc_panel_ilastik_col].tolist(),
        }
    )
    metal_order = imc_panel[imc_panel_metal_col].tolist()
    return panel, metal_order


def preprocess_images(
    mcd_files: Sequence[Union[str, PathLike]],
    txt_files: Sequence[Union[str, PathLike]],
    metal_order: Sequence[str],
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
                    img = data.get_image_stack_by_names(metal_order)
                    img = preprocess_image(img, hpf=hpf)
                    yield mcd_file, acquisition.id, img
    while len(remaining_txt_files) > 0:
        txt_file = Path(remaining_txt_files.pop(0))
        with TxtParser(txt_file) as txt_parser:
            data = txt_parser.get_acquisition_data()
        if data.is_valid:
            img = data.get_image_stack_by_names(metal_order)
            img = preprocess_image(img, hpf=hpf)
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
