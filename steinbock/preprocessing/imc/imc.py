import logging
import numpy as np
import pandas as pd

from imctools.data.acquisition import Acquisition
from imctools.io.mcd.mcdparser import McdParser
from imctools.io.txt.txtparser import TxtParser
from os import PathLike
from pathlib import Path
from scipy.ndimage import maximum_filter
from typing import Generator, List, Optional, Sequence, Tuple, Union

from steinbock.classification.ilastik import ilastik
from steinbock.utils import io


logger = logging.getLogger(__name__)

imc_panel_metal_col = "Metal Tag"
imc_panel_name_col = "Target"
imc_panel_enable_col = "full"
imc_panel_ilastik_col = "ilastik"

required_imc_panel_cols = (
    imc_panel_metal_col,
    imc_panel_name_col,
    imc_panel_enable_col,
    imc_panel_ilastik_col,
)


def list_mcd_files(mcd_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(mcd_dir).rglob("*.mcd"))


def list_txt_files(mcd_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(mcd_dir).rglob("*.txt"))


def parse_imc_panel(
    imc_panel_file: Union[str, Path],
) -> Tuple[pd.DataFrame, List[str]]:

    imc_panel = pd.read_csv(imc_panel_file)
    for imc_panel_col in required_imc_panel_cols:
        if imc_panel_col not in imc_panel:
            raise ValueError(f"Missing column in IMC panel: {imc_panel_col}")
    panel = imc_panel.loc[imc_panel[imc_panel_enable_col].astype(bool), :]
    panel.drop(columns=imc_panel_enable_col, inplace=True)
    panel.sort_values(
        imc_panel_metal_col,
        key=lambda s: pd.to_numeric(s.str.replace("[^0-9]", "", regex=True)),
        inplace=True,
    )
    m = panel[imc_panel_ilastik_col].astype(bool)
    panel[imc_panel_ilastik_col] = pd.Series(dtype=pd.UInt8Dtype())
    panel.loc[m, imc_panel_ilastik_col] = range(1, m.sum() + 1)
    panel.rename(
        columns={
            imc_panel_name_col: io.panel_name_col,
            imc_panel_ilastik_col: ilastik.panel_ilastik_col,
        },
        inplace=True,
    )
    col_order = panel.columns.tolist()
    col_order.remove(io.panel_name_col)
    col_order.remove(ilastik.panel_ilastik_col)
    col_order.insert(0, io.panel_name_col)
    col_order.insert(1, ilastik.panel_ilastik_col)
    metal_order = panel[imc_panel_metal_col].tolist()
    return panel.loc[:, col_order], metal_order


def create_panel_from_mcd(
    mcd_file: Union[str, Path],
) -> Tuple[pd.DataFrame, List[str]]:
    with McdParser(mcd_file) as mcd_parser:
        acquisition = next(iter(mcd_parser.session.acquisitions.values()))
        return create_panel_from_acquisition(acquisition)


def create_panel_from_txt(
    txt_file: Union[str, Path],
) -> Tuple[pd.DataFrame, List[str]]:
    with TxtParser(txt_file) as txt_parser:
        acquisition = txt_parser.get_acquisition_data().acquisition
        return create_panel_from_acquisition(acquisition)


def create_panel_from_acquisition(
    acquisition: Acquisition,
) -> Tuple[pd.DataFrame, List[str]]:
    channels = sorted(
        acquisition.channels.values(),
        key=lambda channel: channel.order_number,
    )
    panel = pd.DataFrame(
        data={
            io.panel_name_col: [channel.label for channel in channels],
            ilastik.panel_ilastik_col: range(1, len(channels) + 1),
            "metal": [channel.name for channel in channels],
        }
    )
    panel.sort_values(
        "metal",
        key=lambda s: pd.to_numeric(s.str.replace("[^0-9]", "", regex=True)),
        inplace=True,
    )
    return panel, panel["metal"].tolist()


def preprocess_images(
    mcd_files: Sequence[Union[str, PathLike]],
    txt_files: Sequence[Union[str, PathLike]],
    metal_order: Optional[Sequence[str]] = None,
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
                    img = data.image_data
                    if metal_order is not None:
                        img = data.get_image_stack_by_names(metal_order)
                    img = preprocess_image(img, hpf=hpf)
                    yield mcd_file, acquisition.id, img
                    del img
    while len(remaining_txt_files) > 0:
        txt_file = Path(remaining_txt_files.pop(0))
        with TxtParser(txt_file) as txt_parser:
            data = txt_parser.get_acquisition_data()
        if data.image_data is not None and data.is_valid:
            img = data.image_data
            if metal_order is not None:
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
