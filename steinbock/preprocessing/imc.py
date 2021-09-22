import logging
import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from scipy.ndimage import maximum_filter
from typing import (
    Generator,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from steinbock import io

try:
    from imctools.data.acquisition import Acquisition as _Acquisition
    from imctools.data.acquisitiondata import (
        AcquisitionData as _AcquisitionData,
    )
    from imctools.io.mcd.mcdparser import McdParser as _McdParser
    from imctools.io.txt.txtparser import TxtParser as _TxtParser

    imc_available = True
except:
    imc_available = False


class Acquisition(NamedTuple):
    id: int
    description: str
    posx_um: float
    posy_um: float
    width_um: float
    height_um: float


_imc_panel_metal_col = "Metal Tag"
_imc_panel_target_col = "Target"
_imc_panel_keep_col = "full"
_imc_panel_ilastik_col = "ilastik"
_imc_panel_deepcell_col = "deepcell"
_logger = logging.getLogger(__name__)


def list_mcd_files(mcd_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(mcd_dir).rglob("*.mcd"))


def list_txt_files(mcd_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(mcd_dir).rglob("*.txt"))


def create_panel_from_imc_panel(
    imc_panel_file: Union[str, PathLike]
) -> pd.DataFrame:
    imc_panel = pd.read_csv(
        imc_panel_file,
        sep=",|;",
        dtype={
            _imc_panel_metal_col: pd.StringDtype(),
            _imc_panel_target_col: pd.StringDtype(),
            _imc_panel_keep_col: pd.BooleanDtype(),
            _imc_panel_ilastik_col: pd.BooleanDtype(),
            _imc_panel_deepcell_col: pd.BooleanDtype(),
        },
        engine="python",
        true_values=["1"],
        false_values=["0"],
    )
    for required_col in (_imc_panel_metal_col, _imc_panel_target_col):
        if required_col not in imc_panel:
            raise ValueError(f"Missing '{required_col}' column in IMC panel")
    for notnan_col in (
        _imc_panel_metal_col,
        _imc_panel_keep_col,
        _imc_panel_ilastik_col,
        _imc_panel_deepcell_col,
    ):
        if notnan_col in imc_panel and imc_panel[notnan_col].isna().any():
            raise ValueError(f"Missing values for '{notnan_col}' in IMC panel")
    panel = imc_panel.rename(
        columns={
            _imc_panel_metal_col: "channel",
            _imc_panel_target_col: "name",
            _imc_panel_keep_col: "keep",
            _imc_panel_ilastik_col: "ilastik",
            _imc_panel_deepcell_col: "deepcell",
        }
    )
    for _, group in panel.groupby("channel"):
        panel.loc[group.index, "name"] = "/".join(
            group["name"].dropna().unique()
        )
        if "keep" in panel:
            panel.loc[group.index, "keep"] = group["keep"].any()
        if "ilastik" in panel:
            panel.loc[group.index, "ilastik"] = group["ilastik"].any()
        if "deepcell" in panel:
            panel.loc[group.index, "deepcell"] = group["deepcell"].any()
    panel = panel.groupby(panel["channel"].values).aggregate("first")
    panel.sort_values(
        "channel",
        key=lambda s: pd.to_numeric(s.str.replace("[^0-9]", "", regex=True)),
        inplace=True,
    )
    if "keep" not in panel:
        panel["keep"] = pd.Series(True, dtype=pd.BooleanDtype())
    if "ilastik" in panel:
        ilastik_mask = panel["ilastik"].astype(bool)
        panel["ilastik"] = pd.Series(dtype=pd.UInt8Dtype())
        panel.loc[ilastik_mask, "ilastik"] = range(1, ilastik_mask.sum() + 1)
    else:
        panel["ilastik"] = pd.Series(
            range(1, len(panel.index) + 1), dtype=pd.UInt8Dtype()
        )
    if "deepcell" in panel:
        deepcell_mask = panel["deepcell"].astype(bool)
        panel["deepcell"] = pd.Series(dtype=pd.UInt8Dtype())
        panel.loc[deepcell_mask, "deepcell"] = range(
            1, deepcell_mask.sum() + 1
        )
    else:
        panel["deepcell"] = pd.Series(
            range(1, len(panel.index) + 1), dtype=pd.UInt8Dtype()
        )
    col_order = panel.columns.tolist()
    next_col_index = 0
    for col in ("channel", "name", "keep", "ilastik", "deepcell"):
        if col in col_order:
            col_order.remove(col)
            col_order.insert(next_col_index, col)
            next_col_index += 1
    panel = panel.loc[:, col_order]
    return panel


def create_panel_from_mcd_file(mcd_file: Union[str, PathLike]) -> pd.DataFrame:
    with _McdParser(mcd_file) as mcd_parser:
        acquisition = next(iter(mcd_parser.session.acquisitions.values()))
        return create_panel_from_acquisition(acquisition)


def create_panel_from_txt_file(txt_file: Union[str, PathLike]) -> pd.DataFrame:
    with _TxtParser(txt_file) as txt_parser:
        acquisition = txt_parser.get_acquisition_data().acquisition
        return create_panel_from_acquisition(acquisition)


def create_panel_from_acquisition(acquisition: "_Acquisition") -> pd.DataFrame:
    channels = sorted(
        acquisition.channels.values(), key=lambda channel: channel.order_number
    )
    panel = pd.DataFrame(
        data={
            "channel": [channel.name for channel in channels],
            "name": [channel.label for channel in channels],
            "keep": 1,
            "ilastik": range(1, len(channels) + 1),
            "deepcell": np.nan,
        }
    )
    panel.sort_values(
        "channel",
        key=lambda s: pd.to_numeric(s.str.replace("[^0-9]", "", regex=True)),
        inplace=True,
    )
    return panel


def filter_hot_pixels(img: np.ndarray, thres: float) -> np.ndarray:
    kernel = np.ones((1, 3, 3), dtype=bool)
    kernel[0, 1, 1] = False
    max_neighbor_img = maximum_filter(img, footprint=kernel, mode="mirror")
    return np.where(img - max_neighbor_img > thres, max_neighbor_img, img)


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


def try_preprocess_images_from_disk(
    mcd_files: Sequence[Union[str, PathLike]],
    txt_files: Sequence[Union[str, PathLike]],
    metal_order: Optional[Sequence[str]] = None,
    hpf: Optional[float] = None,
) -> Generator[Tuple[Path, Optional[Acquisition], np.ndarray], None, None]:
    def data_is_valid(data: "_AcquisitionData") -> bool:
        return (
            data is not None and data.image_data is not None and data.is_valid
        )

    def preprocess_data(data: "_AcquisitionData") -> np.ndarray:
        img = data.image_data
        if metal_order is not None:
            img = data.get_image_stack_by_names(metal_order)
        img = preprocess_image(img, hpf=hpf)
        return io.to_dtype(img, io.img_dtype)

    remaining_txt_files = list(txt_files)
    for mcd_file in mcd_files:
        try:
            with _McdParser(mcd_file) as mcd_parser:
                for a in mcd_parser.session.acquisitions.values():
                    txt_file = None
                    filtered_txt_files = [
                        x
                        for x in remaining_txt_files
                        if Path(x).stem.startswith(Path(mcd_file).stem)
                        and Path(x).stem.endswith(f"_{a.id}")
                    ]
                    if len(filtered_txt_files) == 1:
                        txt_file = filtered_txt_files[0]
                        remaining_txt_files.remove(txt_file)
                    try:
                        data = mcd_parser.get_acquisition_data(a.id)
                        if not data_is_valid(data):
                            _logger.warning(f"File corrupted: {mcd_file}")
                            if txt_file is not None:
                                _logger.info(f"Restoring from file {txt_file}")
                                try:
                                    with _TxtParser(
                                        txt_file, slide_id=a.slide_id
                                    ) as txt_parser:
                                        data = (
                                            txt_parser.get_acquisition_data()
                                        )
                                        if not data_is_valid(data):
                                            _logger.warning(
                                                f"File corrupted: {txt_file}"
                                            )
                                except:
                                    _logger.exception(
                                        f"Error preprocessing file {txt_file}"
                                    )
                        if data_is_valid(data):
                            img = preprocess_data(data)
                            acquisition = Acquisition(
                                a.id,
                                a.description,
                                min(a.roi_start_x_pos_um, a.roi_end_x_pos_um),
                                min(a.roi_start_y_pos_um, a.roi_end_y_pos_um),
                                abs(a.roi_start_x_pos_um - a.roi_end_x_pos_um),
                                abs(a.roi_start_y_pos_um - a.roi_end_y_pos_um),
                            )
                            yield Path(mcd_file), acquisition, img
                            del img
                    except:
                        _logger.exception(
                            f"Error preprocessing acquisition {a.id}"
                            f" from file {mcd_file}"
                        )
        except:
            _logger.exception(f"Error preprocessing file {mcd_file}")
    while len(remaining_txt_files) > 0:
        txt_file = remaining_txt_files.pop(0)
        try:
            with _TxtParser(txt_file) as txt_parser:
                data = txt_parser.get_acquisition_data()
                if not data_is_valid(data):
                    _logger.warning(f"File corrupted: {txt_file}")
            if data_is_valid(data):
                img = preprocess_data(data)
                yield Path(txt_file), None, img
                del img
        except:
            _logger.exception(f"Error preprocessing file {txt_file}")
