import logging
import re
from os import PathLike
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple, Union
from zipfile import ZipFile

import numpy as np
import pandas as pd
from scipy.ndimage import maximum_filter

from .. import io
from ._preprocessing import SteinbockPreprocessingException

try:
    from readimc import MCDFile, TXTFile
    from readimc.data import Acquisition, AcquisitionBase

    imc_available = True
except Exception:
    imc_available = False


logger = logging.getLogger(__name__)


class SteinbockIMCPreprocessingException(SteinbockPreprocessingException):
    pass


def _get_zip_file_member(path: Union[str, PathLike]) -> Optional[Tuple[Path, str]]:
    for parent_path in Path(path).parents:
        if parent_path.suffix == ".zip" and parent_path.is_file():
            member_path = Path(path).relative_to(parent_path)
            return parent_path, str(member_path)
    return None


def list_mcd_files(mcd_dir: Union[str, PathLike], unzip: bool = False) -> List[Path]:
    mcd_files = sorted(Path(mcd_dir).rglob("[!.]*.mcd"))
    if unzip:
        for zip_file in sorted(Path(mcd_dir).rglob("[!.]*.zip")):
            with ZipFile(zip_file) as fzip:
                for zip_info in sorted(fzip.infolist(), key=lambda x: x.filename):
                    if not zip_info.is_dir() and zip_info.filename.endswith(".mcd"):
                        mcd_files.append(zip_file / zip_info.filename)
    return mcd_files


def list_txt_files(txt_dir: Union[str, PathLike], unzip: bool = False) -> List[Path]:
    txt_files = sorted(Path(txt_dir).rglob("[!.]*.txt"))
    if unzip:
        for zip_file in sorted(Path(txt_dir).rglob("[!.]*.zip")):
            with ZipFile(zip_file) as fzip:
                for zip_info in sorted(fzip.infolist(), key=lambda x: x.filename):
                    if not zip_info.is_dir() and zip_info.filename.endswith(".txt"):
                        txt_files.append(zip_file / zip_info.filename)
    return txt_files


def _clean_panel(panel: pd.DataFrame) -> pd.DataFrame:
    panel.sort_values(
        "channel",
        key=lambda s: pd.to_numeric(s.str.replace("[^0-9]", "", regex=True)),
        inplace=True,
    )
    name_dupl_mask = panel["name"].duplicated(keep=False)
    name_suffixes = panel.groupby("name").cumcount().map(lambda i: f" {i + 1}")
    panel.loc[name_dupl_mask, "name"] += name_suffixes[name_dupl_mask]
    if "keep" not in panel:
        panel["keep"] = pd.Series([True] * len(panel.index), dtype=pd.BooleanDtype())
    if "ilastik" not in panel:
        panel["ilastik"] = pd.Series(dtype=pd.UInt8Dtype())
        panel.loc[panel["keep"], "ilastik"] = range(1, panel["keep"].sum() + 1)
    if "deepcell" not in panel:
        panel["deepcell"] = pd.Series(dtype=pd.UInt8Dtype())
    if "cellpose" not in panel:
        panel["cellpose"] = pd.Series(dtype=pd.UInt8Dtype())
    next_column_index = 0
    for column in ("channel", "name", "keep", "ilastik", "deepcell", "cellpose"):
        if column in panel:
            column_data = panel[column]
            panel.drop(columns=[column], inplace=True)
            panel.insert(next_column_index, column, column_data)
            next_column_index += 1
    return panel


def create_panel_from_imc_panel(
    imc_panel_file: Union[str, PathLike],
    imc_panel_channel_col: str = "Metal Tag",
    imc_panel_name_col: str = "Target",
    imc_panel_keep_col: str = "full",
    imc_panel_ilastik_col: str = "ilastik",
) -> pd.DataFrame:
    imc_panel = pd.read_csv(
        imc_panel_file,
        sep=",|;",
        dtype={
            imc_panel_channel_col: pd.StringDtype(),
            imc_panel_name_col: pd.StringDtype(),
            imc_panel_keep_col: pd.BooleanDtype(),
            imc_panel_ilastik_col: pd.BooleanDtype(),
        },
        engine="python",
        true_values=["1"],
        false_values=["0"],
    )
    for required_col in (imc_panel_channel_col, imc_panel_name_col):
        if required_col not in imc_panel:
            raise SteinbockIMCPreprocessingException(
                f"Missing '{required_col}' column in IMC panel"
            )
    for notnan_col in (
        imc_panel_channel_col,
        imc_panel_keep_col,
        imc_panel_ilastik_col,
    ):
        if notnan_col in imc_panel and imc_panel[notnan_col].isna().any():
            raise SteinbockIMCPreprocessingException(
                f"Missing values for '{notnan_col}' in IMC panel"
            )
    rename_columns = {
        imc_panel_channel_col: "channel",
        imc_panel_name_col: "name",
        imc_panel_keep_col: "keep",
        imc_panel_ilastik_col: "ilastik",
    }
    drop_columns = [
        panel_col
        for imc_panel_col, panel_col in rename_columns.items()
        if panel_col in imc_panel.columns and panel_col != imc_panel_col
    ]
    panel = imc_panel.drop(columns=drop_columns).rename(columns=rename_columns)
    for _, g in panel.groupby("channel"):
        panel.loc[g.index, "name"] = " / ".join(g["name"].dropna().unique())
        if "keep" in panel:
            panel.loc[g.index, "keep"] = g["keep"].any()
        if "ilastik" in panel:
            panel.loc[g.index, "ilastik"] = g["ilastik"].any()
    panel = panel.groupby(panel["channel"].values).aggregate("first")
    panel = _clean_panel(panel)  # ilastik column may be nullable uint8 now
    ilastik_mask = panel["ilastik"].fillna(False).astype(bool)
    panel["ilastik"] = pd.Series(dtype=pd.UInt8Dtype())
    panel.loc[ilastik_mask, "ilastik"] = range(1, ilastik_mask.sum() + 1)
    return panel


def create_panels_from_mcd_file(mcd_file: Union[str, PathLike]) -> List[pd.DataFrame]:
    panels = []
    with MCDFile(mcd_file) as f:
        for slide in f.slides:
            for acquisition in slide.acquisitions:
                panel = pd.DataFrame(
                    data={
                        "channel": pd.Series(
                            data=acquisition.channel_names,
                            dtype=pd.StringDtype(),
                        ),
                        "name": pd.Series(
                            data=acquisition.channel_labels,
                            dtype=pd.StringDtype(),
                        ),
                    },
                )
                panels.append(panel)
    return panels


def create_panel_from_mcd_files(
    mcd_files: Sequence[Union[str, PathLike]], unzip: bool = False
) -> pd.DataFrame:
    panels = []
    for mcd_file in mcd_files:
        zip_file_mcd_member = _get_zip_file_member(mcd_file)
        if zip_file_mcd_member is None:
            panels += create_panels_from_mcd_file(mcd_file)
        elif unzip:
            zip_file, mcd_member = zip_file_mcd_member
            with ZipFile(zip_file) as fzip:
                with TemporaryDirectory() as temp_dir:
                    extracted_mcd_file = fzip.extract(mcd_member, path=temp_dir)
                    panels += create_panels_from_mcd_file(extracted_mcd_file)
    panel = pd.concat(panels, ignore_index=True, copy=False)
    panel.drop_duplicates(inplace=True, ignore_index=True)
    return _clean_panel(panel)


def create_panel_from_txt_file(txt_file: Union[str, PathLike]) -> pd.DataFrame:
    with TXTFile(txt_file) as f:
        return pd.DataFrame(
            data={
                "channel": pd.Series(data=f.channel_names, dtype=pd.StringDtype()),
                "name": pd.Series(data=f.channel_labels, dtype=pd.StringDtype()),
            },
        )


def create_panel_from_txt_files(
    txt_files: Sequence[Union[str, PathLike]], unzip: bool = False
) -> pd.DataFrame:
    panels = []
    for txt_file in txt_files:
        zip_file_txt_member = _get_zip_file_member(txt_file)
        if zip_file_txt_member is None:
            panel = create_panel_from_txt_file(txt_file)
            panels.append(panel)
        elif unzip:
            zip_file, txt_member = zip_file_txt_member
            with ZipFile(zip_file) as fzip:
                with TemporaryDirectory() as temp_dir:
                    extracted_txt_file = fzip.extract(txt_member, path=temp_dir)
                    panel = create_panel_from_txt_file(extracted_txt_file)
                    panels.append(panel)
    panel = pd.concat(panels, ignore_index=True, copy=False)
    panel.drop_duplicates(inplace=True, ignore_index=True)
    return _clean_panel(panel)


def create_image_info(
    mcd_txt_file: Union[str, PathLike],
    acquisition: Optional[Acquisition],
    img: np.ndarray,
    recovery_file: Union[str, PathLike, None],
    recovered: bool,
    img_file: Union[str, PathLike],
) -> Dict[str, Any]:
    recovery_file_name = None
    if recovery_file is not None:
        recovery_file_name = Path(recovery_file).name
    image_info_row = {
        "image": Path(img_file).name,
        "width_px": img.shape[2],
        "height_px": img.shape[1],
        "num_channels": img.shape[0],
        "source_file": Path(mcd_txt_file).name,
        "recovery_file": recovery_file_name,
        "recovered": recovered,
    }
    if acquisition is not None:
        image_info_row.update(
            {
                "acquisition_id": acquisition.id,
                "acquisition_description": acquisition.description,
                "acquisition_start_x_um": (acquisition.roi_points_um[0][0]),
                "acquisition_start_y_um": (acquisition.roi_points_um[0][1]),
                "acquisition_end_x_um": (acquisition.roi_points_um[2][0]),
                "acquisition_end_y_um": (acquisition.roi_points_um[2][1]),
                "acquisition_width_um": acquisition.width_um,
                "acquisition_height_um": acquisition.height_um,
            }
        )
    return image_info_row


def filter_hot_pixels(img: np.ndarray, thres: float) -> np.ndarray:
    kernel = np.ones((1, 3, 3), dtype=bool)
    kernel[0, 1, 1] = False
    max_neighbor_img = maximum_filter(img, footprint=kernel, mode="mirror")
    return np.where(img - max_neighbor_img > thres, max_neighbor_img, img)


def preprocess_image(img: np.ndarray, hpf: Optional[float] = None) -> np.ndarray:
    img = img.astype(np.float32)
    if hpf is not None:
        img = filter_hot_pixels(img, hpf)
    return io._to_dtype(img, io.img_dtype)


def _get_channel_indices(
    acquisition: AcquisitionBase, channel_names: Sequence[str]
) -> Union[List[int], str]:
    channel_indices = []
    for channel_name in channel_names:
        if channel_name not in acquisition.channel_names:
            return channel_name
        channel_indices.append(acquisition.channel_names.index(channel_name))
    return channel_indices


def _match_txt_file(
    mcd_file: Union[str, PathLike],
    acquisition: Acquisition,
    txt_files: Sequence[Union[str, PathLike]],
) -> Union[str, PathLike, None]:
    txt_file_name_pattern = re.compile(
        rf"{Path(mcd_file).stem}.*_0*{acquisition.id}.txt"
    )
    filtered_txt_files = [
        txt_file
        for txt_file in txt_files
        if txt_file_name_pattern.match(Path(txt_file).name)
    ]
    if len(filtered_txt_files) == 1:
        return filtered_txt_files[0]
    if len(filtered_txt_files) > 1:
        logger.warning(
            "Ambiguous txt file matching for %s: %s; continuing without a match",
            mcd_file,
            ", ".join(str(x) for x in filtered_txt_files),
        )
    return None


def _try_preprocess_txt_image_from_disk(
    txt_file: Union[str, PathLike],
    channel_names: Optional[Sequence[str]] = None,
    hpf: Optional[float] = None,
) -> Optional[np.ndarray]:
    try:
        channel_ind = None
        with TXTFile(txt_file) as f:
            if channel_names is not None:
                channel_ind = _get_channel_indices(f, channel_names)
                if isinstance(channel_ind, str):
                    logger.warning(
                        f"Channel {channel_ind} not found in file {txt_file}; skipping"
                    )
                    return None
            img = f.read_acquisition()
        if channel_ind is not None:
            img = img[channel_ind, :, :]
        img = preprocess_image(img, hpf=hpf)
        return img
    except Exception as e:
        logger.exception(f"Error reading file {txt_file}: {e}")
        return None


def _try_preprocess_mcd_images_from_disk(
    mcd_file: Union[str, PathLike],
    candidate_txt_files: List[Union[str, PathLike]],
    channel_names: Optional[Sequence[str]] = None,
    hpf: Optional[float] = None,
    unzip: bool = False,
) -> Generator[Tuple[Acquisition, np.ndarray, Optional[Path], bool], None, None]:
    try:
        with MCDFile(mcd_file) as f_mcd:
            for slide in f_mcd.slides:
                for acquisition in slide.acquisitions:
                    recovery_txt_file = _match_txt_file(
                        mcd_file, acquisition, candidate_txt_files
                    )
                    if recovery_txt_file is not None:
                        candidate_txt_files.remove(recovery_txt_file)
                        recovery_txt_file = Path(recovery_txt_file)
                    channel_ind = None
                    if channel_names is not None:
                        channel_ind = _get_channel_indices(acquisition, channel_names)
                        if isinstance(channel_ind, str):
                            logger.warning(
                                f"Channel {channel_ind} not found for acquisition "
                                f"{acquisition.id} in file {mcd_file}; skipping"
                            )
                            continue
                    try:
                        img = f_mcd.read_acquisition(acquisition)
                        if channel_ind is not None:
                            img = img[channel_ind, :, :]
                        img = preprocess_image(img, hpf=hpf)
                        yield acquisition, img, recovery_txt_file, False
                        del img
                    except Exception as e:
                        logger.warning(
                            f"Error reading acquisition {acquisition.id} "
                            f"from file {mcd_file}: {e}"
                        )
                        if recovery_txt_file is not None:
                            logger.warning(f"Recovering from file {recovery_txt_file}")
                            zip_file_txt_member = _get_zip_file_member(
                                recovery_txt_file
                            )
                            if zip_file_txt_member is None:
                                img = _try_preprocess_txt_image_from_disk(
                                    recovery_txt_file,
                                    channel_names=channel_names,
                                    hpf=hpf,
                                )
                                if img is not None:
                                    yield acquisition, img, recovery_txt_file, True
                                    del img
                            elif unzip:
                                zip_file, txt_member = zip_file_txt_member
                                with ZipFile(zip_file) as fzip:
                                    with TemporaryDirectory() as temp_dir:
                                        extracted_recovery_txt_file = fzip.extract(
                                            txt_member, path=temp_dir
                                        )
                                        img = _try_preprocess_txt_image_from_disk(
                                            extracted_recovery_txt_file,
                                            channel_names=channel_names,
                                            hpf=hpf,
                                        )
                                        if img is not None:
                                            yield (
                                                acquisition,
                                                img,
                                                recovery_txt_file,
                                                True,
                                            )
                                            del img
    except Exception as e:
        logger.exception(f"Error reading file {mcd_file}: {e}")


def try_preprocess_images_from_disk(
    mcd_files: Sequence[Union[str, PathLike]],
    txt_files: Sequence[Union[str, PathLike]],
    channel_names: Optional[Sequence[str]] = None,
    hpf: Optional[float] = None,
    unzip: bool = False,
) -> Generator[
    Tuple[Path, Optional["Acquisition"], np.ndarray, Optional[Path], bool],
    None,
    None,
]:
    candidate_txt_files = list(txt_files)
    # process mcd files in reverse order to avoid ambiguous txt file matching
    # see https://github.com/BodenmillerGroup/steinbock/issues/100
    for mcd_file in sorted(
        mcd_files, key=lambda mcd_file: Path(mcd_file).stem, reverse=True
    ):
        zip_file_mcd_member = _get_zip_file_member(mcd_file)
        if zip_file_mcd_member is None:
            for (
                acquisition,
                img,
                recovery_txt_file,
                recovered,
            ) in _try_preprocess_mcd_images_from_disk(
                mcd_file,
                candidate_txt_files,
                channel_names=channel_names,
                hpf=hpf,
                unzip=unzip,
            ):
                yield Path(mcd_file), acquisition, img, recovery_txt_file, recovered
                del img
        elif unzip:
            zip_file, mcd_member = zip_file_mcd_member
            with ZipFile(zip_file) as fzip:
                with TemporaryDirectory() as temp_dir:
                    extracted_mcd_file = fzip.extract(mcd_member, path=temp_dir)
                    for (
                        acquisition,
                        img,
                        recovery_txt_file,
                        recovered,
                    ) in _try_preprocess_mcd_images_from_disk(
                        extracted_mcd_file,
                        candidate_txt_files,
                        channel_names=channel_names,
                        hpf=hpf,
                        unzip=unzip,
                    ):
                        yield (
                            Path(mcd_file),
                            acquisition,
                            img,
                            recovery_txt_file,
                            recovered,
                        )
                        del img
    for txt_file in candidate_txt_files:
        zip_file_txt_member = _get_zip_file_member(txt_file)
        if zip_file_txt_member is None:
            img = _try_preprocess_txt_image_from_disk(
                txt_file, channel_names=channel_names, hpf=hpf
            )
            if img is not None:
                yield Path(txt_file), None, img, None, False
                del img
        elif unzip:
            zip_file, txt_member = zip_file_txt_member
            with ZipFile(zip_file) as fzip:
                with TemporaryDirectory() as temp_dir:
                    extracted_txt_file = fzip.extract(txt_member, path=temp_dir)
                    img = _try_preprocess_txt_image_from_disk(
                        extracted_txt_file, channel_names=channel_names, hpf=hpf
                    )
                    if img is not None:
                        yield Path(txt_file), None, img, None, False
                        del img
