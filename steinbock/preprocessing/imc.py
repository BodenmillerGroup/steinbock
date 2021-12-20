import logging
import numpy as np
import pandas as pd
import re

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
    from readimc import MCDFile, TXTFile
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


def list_txt_files(txt_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(txt_dir).rglob("*.txt"))


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
    rename_columns = {
        _imc_panel_metal_col: "channel",
        _imc_panel_target_col: "name",
        _imc_panel_keep_col: "keep",
        _imc_panel_ilastik_col: "ilastik",
        _imc_panel_deepcell_col: "deepcell",
    }
    drop_columns = [
        panel_col
        for imc_panel_col, panel_col in rename_columns.items()
        if panel_col in imc_panel.columns and panel_col != imc_panel_col
    ]
    panel = imc_panel.drop(columns=drop_columns).rename(columns=rename_columns)
    if "ilastik" in panel:
        ilastik_mask = panel["ilastik"].astype(bool)
        panel["ilastik"] = pd.Series(dtype=pd.UInt8Dtype())
        panel.loc[ilastik_mask, "ilastik"] = range(1, ilastik_mask.sum() + 1)
    if "deepcell" in panel:
        deepcell_mask = panel["deepcell"].astype(bool)
        panel["deepcell"] = pd.Series(dtype=pd.UInt8Dtype())
        panel.loc[deepcell_mask, "deepcell"] = range(
            1, deepcell_mask.sum() + 1
        )
    return _clean_panel(panel)


def create_panel_from_mcd_files(
    mcd_files: Sequence[Union[str, PathLike]]
) -> pd.DataFrame:
    panels = []
    for mcd_file in mcd_files:
        with MCDFile(mcd_file) as f:
            for slide in f.slides:
                for acquisition in slide.acquisitions:
                    panel = _create_panel_from_acquisition(acquisition)
                    panels.append(panel)
    panel = pd.concat(panels, ignore_index=True, copy=False)
    return _clean_panel(panel)


def create_panel_from_txt_files(
    txt_files: Sequence[Union[str, PathLike]]
) -> pd.DataFrame:
    panels = []
    for txt_file in txt_files:
        with TXTFile(txt_file) as f:
            panel = _create_panel_from_acquisition(f)
            panels.append(panel)
    panel = pd.concat(panels, ignore_index=True, copy=False)
    return _clean_panel(panel)


def filter_hot_pixels(img: np.ndarray, thres: float) -> np.ndarray:
    kernel = np.ones((1, 3, 3), dtype=bool)
    kernel[0, 1, 1] = False
    max_neighbor_img = maximum_filter(img, footprint=kernel, mode="mirror")
    return np.where(img - max_neighbor_img > thres, max_neighbor_img, img)


def preprocess_image(
    img: np.ndarray, hpf: Optional[float] = None
) -> np.ndarray:
    img = img.astype(np.float32)
    if hpf is not None:
        img = filter_hot_pixels(img, hpf)
    return io._to_dtype(img, io.img_dtype)


def try_preprocess_images_from_disk(
    mcd_files: Sequence[Union[str, PathLike]],
    txt_files: Sequence[Union[str, PathLike]],
    channel_names: Optional[Sequence[str]] = None,
    hpf: Optional[float] = None,
) -> Generator[
    Tuple[Path, Optional["Acquisition"], np.ndarray, Optional[Path], bool],
    None,
    None,
]:
    unmatched_txt_files = list(txt_files)
    for mcd_file in mcd_files:
        try:
            with MCDFile(mcd_file) as f_mcd:
                for slide in f_mcd.slides:
                    for acquisition in slide.acquisitions:
                        matched_txt_file = _match_txt_file(
                            mcd_file, acquisition, unmatched_txt_files
                        )
                        if matched_txt_file is not None:
                            unmatched_txt_files.remove(matched_txt_file)
                        channel_ind = None
                        if channel_names is not None:
                            channel_ind = _get_channel_indices(
                                acquisition, channel_names
                            )
                            if isinstance(channel_ind, str):
                                _logger.warning(
                                    f"Channel {channel_ind} not found for "
                                    f"acquisition {acquisition.id} in file "
                                    "{mcd_file}; skipping acquisition"
                                )
                                continue
                        img = None
                        recovered = False
                        try:
                            img = f_mcd.read_acquisition(acquisition)
                        except IOError:
                            _logger.warning(
                                f"Error reading acquisition {acquisition.id} "
                                f"from file {mcd_file}"
                            )
                            if matched_txt_file is not None:
                                _logger.warning(
                                    f"Restoring from file {matched_txt_file}"
                                )
                                try:
                                    with TXTFile(matched_txt_file) as f_txt:
                                        img = f_txt.read_acquisition()
                                        if channel_names is not None:
                                            channel_ind = _get_channel_indices(
                                                f_txt, channel_names
                                            )
                                            if isinstance(channel_ind, str):
                                                _logger.warning(
                                                    f"Channel {channel_ind} "
                                                    "not found in file "
                                                    f"{matched_txt_file}; "
                                                    "skipping acquisition"
                                                )
                                                continue
                                    recovered = True
                                except IOError:
                                    _logger.exception(
                                        "Error reading file "
                                        f"{matched_txt_file}"
                                    )
                        if img is not None:  # exceptions ...
                            if channel_ind is not None:
                                img = img[channel_ind, :, :]
                            img = preprocess_image(img, hpf=hpf)
                            yield (
                                Path(mcd_file),
                                acquisition,
                                img,
                                Path(matched_txt_file)
                                if matched_txt_file is not None
                                else None,
                                recovered,
                            )
                            del img
        except:
            _logger.exception(f"Error reading file {mcd_file}")
    while len(unmatched_txt_files) > 0:
        txt_file = unmatched_txt_files.pop(0)
        try:
            channel_ind = None
            with TXTFile(txt_file) as f:
                if channel_names is not None:
                    channel_ind = _get_channel_indices(f, channel_names)
                    if isinstance(channel_ind, str):
                        _logger.warning(
                            f"Channel {channel_ind} not found in file "
                            f"{txt_file}; skipping acquisition"
                        )
                        continue
                img = f.read_acquisition()
            if channel_ind is not None:
                img = img[channel_ind, :, :]
            img = preprocess_image(img, hpf=hpf)
            yield Path(txt_file), None, img, None, False
            del img
        except:
            _logger.exception(f"Error reading file {txt_file}")


def _create_panel_from_acquisition(
    acquisition: "AcquisitionBase",
) -> pd.DataFrame:
    panel = pd.DataFrame(
        data={
            "channel": acquisition.channel_names,
            "name": acquisition.channel_labels,
            "keep": True,
            "ilastik": range(1, acquisition.num_channels + 1),
            "deepcell": np.nan,
        },
    )
    panel["channel"] = panel["channel"].astype(pd.StringDtype())
    panel["name"] = panel["name"].astype(pd.StringDtype())
    panel["keep"] = panel["keep"].astype(pd.BooleanDtype())
    panel["ilastik"] = panel["ilastik"].astype(pd.UInt8Dtype())
    panel["deepcell"] = panel["deepcell"].astype(pd.UInt8Dtype())
    panel.sort_values(
        "channel",
        key=lambda s: pd.to_numeric(s.str.replace("[^0-9]", "", regex=True)),
        inplace=True,
    )
    return panel


def _clean_panel(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    for _, g in panel.groupby("channel"):
        panel.loc[g.index, "name"] = " / ".join(g["name"].dropna().unique())
        if "keep" in panel:
            panel.loc[g.index, "keep"] = g["keep"].any()
        if "ilastik" in panel:
            panel.loc[g.index, "ilastik"] = g["ilastik"].notna().any()
        if "deepcell" in panel:
            panel.loc[g.index, "deepcell"] = g["deepcell"].notna().any()
    panel = panel.groupby(panel["channel"].values).aggregate("first")
    panel.sort_values(
        "channel",
        key=lambda s: pd.to_numeric(s.str.replace("[^0-9]", "", regex=True)),
        inplace=True,
    )
    name_dupl_mask = panel["name"].duplicated(keep=False)
    name_suffixes = panel.groupby("name").cumcount().map(lambda i: f" {i + 1}")
    panel.loc[name_dupl_mask, "name"] += name_suffixes[name_dupl_mask]
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
    next_column_index = 0
    for column in ("channel", "name", "keep", "ilastik", "deepcell"):
        if column in panel:
            column_data = panel[column]
            panel.drop(columns=[column], inplace=True)
            panel.insert(next_column_index, column, column_data)
            next_column_index += 1
    return panel


def _match_txt_file(
    mcd_file: Union[str, PathLike],
    acquisition: Acquisition,
    txt_files: Sequence[Union[str, PathLike]],
) -> Union[str, PathLike, None]:
    pattern = re.compile(rf"{Path(mcd_file).stem}.*_0*{acquisition.id}.txt")
    filtered_txt_files = [
        txt_file
        for txt_file in txt_files
        if pattern.match(Path(txt_file).name)
    ]
    if len(filtered_txt_files) == 1:
        return filtered_txt_files[0]
    return None


def _get_channel_indices(
    acquisition: AcquisitionBase, channel_names: Sequence[str]
) -> Union[Sequence[int], str]:
    channel_indices = []
    for channel_name in channel_names:
        if channel_name not in acquisition.channel_names:
            return channel_name
        channel_indices.append(acquisition.channel_names.index(channel_name))
    return channel_indices
