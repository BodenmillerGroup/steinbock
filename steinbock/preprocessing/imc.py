import logging
import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from scipy.ndimage import maximum_filter
from typing import (
    Generator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from steinbock import io

try:
    from readimc import IMCMcdFile, IMCTxtFile
    from readimc.data import Acquisition, AcquisitionBase

    imc_available = True
except:
    imc_available = False


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
    with IMCMcdFile(mcd_file) as f:
        first_slide = f.slides[0]
        first_acquisition = first_slide.acquisitions[0]
        return _create_panel_from_acquisition(first_acquisition)


def create_panel_from_txt_file(txt_file: Union[str, PathLike]) -> pd.DataFrame:
    with IMCTxtFile(txt_file) as f:
        return _create_panel_from_acquisition(f)


def _create_panel_from_acquisition(
    acquisition: "AcquisitionBase",
) -> pd.DataFrame:
    panel = pd.DataFrame(
        data={
            "channel": acquisition.channel_names,
            "name": acquisition.channel_labels,
            "keep": 1,
            "ilastik": range(1, acquisition.num_channels + 1),
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
    channel_order: Optional[Sequence[str]] = None,
    hpf: Optional[float] = None,
) -> Generator[Tuple[Path, Optional["Acquisition"], np.ndarray], None, None]:
    def preprocess(a: AcquisitionBase, img: np.ndarray) -> np.ndarray:
        if channel_order is not None:
            indices = [a.channel_names.index(metal) for metal in channel_order]
            img = img[indices, :, :]
        img = preprocess_image(img, hpf=hpf)
        return io._to_dtype(img, io.img_dtype)

    remaining_txt_files = list(txt_files)
    for mcd_file in mcd_files:
        try:
            with IMCMcdFile(mcd_file) as f_mcd:
                for slide in f_mcd.slides:
                    for acquisition in slide.acquisitions:
                        txt_file = None
                        filtered_txt_files = [
                            x
                            for x in remaining_txt_files
                            if Path(x).stem.startswith(Path(mcd_file).stem)
                            and Path(x).stem.endswith(f"_{acquisition.id}")
                        ]
                        if len(filtered_txt_files) == 1:
                            txt_file = filtered_txt_files[0]
                            remaining_txt_files.remove(txt_file)
                        img = None
                        try:
                            img = f_mcd.read_acquisition(acquisition)
                        except IOError:
                            _logger.warning(
                                f"Error reading acquisition {acquisition.id} "
                                f"from file {mcd_file}"
                            )
                            if txt_file is not None:
                                _logger.info(f"Restoring from file {txt_file}")
                                try:
                                    with IMCTxtFile(txt_file) as f_txt:
                                        img = f_txt.read_acquisition()
                                except IOError:
                                    _logger.exception(
                                        f"Error reading file {txt_file}"
                                    )
                        if img is not None:
                            img = preprocess(acquisition, img)
                            yield Path(mcd_file), acquisition, img
                            del img
        except:
            _logger.exception(f"Error reading file {mcd_file}")
    while len(remaining_txt_files) > 0:
        txt_file = remaining_txt_files.pop(0)
        try:
            with IMCTxtFile(txt_file) as f:
                img = f.read_acquisition()
                img = preprocess(f, img)
            yield Path(txt_file), None, img
            del img
        except:
            _logger.exception(f"Error reading file {txt_file}")
