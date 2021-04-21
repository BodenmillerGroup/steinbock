import logging
import numpy as np
import pandas as pd

from imctools.io.mcd.mcdparser import McdParser
from imctools.io.txt.txtparser import TxtParser
from os import PathLike
from pathlib import Path
from scipy.ndimage import maximum_filter
from typing import Generator, List, Optional, Sequence, Tuple, Union

from steinbock.classification.ilastik import ilastik
from steinbock.utils import io


logger = logging.getLogger(__name__)

panel_metal_col = "Metal Tag"
panel_name_col = "Target"
panel_enable_col = "full"
panel_ilastik_col = "ilastik"

required_panel_cols = (
    panel_metal_col,
    panel_name_col,
    panel_enable_col,
    panel_ilastik_col,
)


def list_mcd_files(mcd_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(mcd_dir).rglob("*.mcd"))


def list_txt_files(mcd_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(mcd_dir).rglob("*.txt"))


def preprocess_panel(
    panel_file: Union[str, Path],
) -> pd.DataFrame:

    panel = pd.read_csv(panel_file)
    for col in required_panel_cols:
        if col not in panel:
            raise ValueError(f"Missing column in IMC panel: {col}")
    panel = panel.loc[panel[panel_enable_col].astype(bool), :]
    panel.drop(columns=panel_enable_col, inplace=True)
    panel.sort_values(
        panel_metal_col,
        key=lambda s: pd.to_numeric(s.str.replace("[^0-9]", "", regex=True)),
        inplace=True,
    )
    m = panel[panel_ilastik_col].astype(bool)
    panel[panel_ilastik_col] = pd.Series(dtype=pd.UInt8Dtype())
    panel.loc[m, panel_ilastik_col] = range(1, m.sum() + 1)
    panel.rename(
        columns={
            panel_name_col: io.panel_name_col,
            panel_ilastik_col: ilastik.panel_ilastik_col,
        },
        inplace=True,
    )
    col_order = panel.columns.tolist()
    col_order.remove(io.panel_name_col)
    col_order.remove(ilastik.panel_ilastik_col)
    col_order.insert(0, io.panel_name_col)
    col_order.insert(1, ilastik.panel_ilastik_col)
    return panel.loc[:, col_order]


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
                    del img
    while len(remaining_txt_files) > 0:
        txt_file = Path(remaining_txt_files.pop(0))
        with TxtParser(txt_file) as txt_parser:
            data = txt_parser.get_acquisition_data()
        if data.is_valid:
            img = data.get_image_stack_by_names(metal_order)
            img = preprocess_image(img, hpf=hpf)
            yield txt_file, None, img
            del img


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
