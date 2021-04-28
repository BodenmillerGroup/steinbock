import numpy as np
import pandas as pd
import tifffile

from os import PathLike
from pathlib import Path
from typing import List, Union

panel_metal_col = "metal"
panel_name_col = "name"
panel_keep_col = "keep"


def read_panel(
    panel_file: Union[str, PathLike],
    kept_only: bool = True,
) -> pd.DataFrame:
    panel_file = Path(panel_file).with_suffix(".csv")
    panel = pd.read_csv(
        panel_file,
        dtype={
            panel_metal_col: pd.StringDtype(),
            panel_name_col: pd.StringDtype(),
            panel_keep_col: pd.BooleanDtype(),
        },
        true_values=["1"],
        false_values=["0"],
    )
    for required_col in (panel_name_col,):
        if required_col not in panel:
            raise ValueError(
                f"Missing '{required_col}' column in panel {panel_file}",
            )
    for notnan_col in (panel_metal_col, panel_name_col, panel_keep_col):
        if notnan_col in panel and panel[notnan_col].isna().any():
            raise ValueError(
                f"Missing values for '{notnan_col}' in panel {panel_file}",
            )
    for unique_col in (panel_metal_col, panel_name_col):
        if unique_col in panel and panel[unique_col].duplicated().any():
            raise ValueError(
                f"Duplicated values for '{unique_col}' in panel {panel_file}",
            )
    if kept_only and panel_keep_col in panel:
        panel = panel.loc[panel[panel_keep_col], :]
    return panel


def write_panel(panel: pd.DataFrame, panel_file: Union[str, PathLike]) -> Path:
    panel_file = Path(panel_file).with_suffix(".csv")
    panel.to_csv(panel_file, index=False)
    return panel_file


def list_images(img_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(img_dir).rglob("*.tiff"))


def read_image(
    img_file: Union[str, PathLike],
    ignore_dtype: bool = False,
) -> np.ndarray:
    img_file = Path(img_file).with_suffix(".tiff")
    img = tifffile.imread(img_file)
    while img.ndim > 3 and img.shape[0] == 1:
        img = img.sqeeze(axis=0)
    while img.ndim > 3 and img.shape[-1] == 1:
        img = img.sqeeze(axis=img.ndim - 1)
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    elif img.ndim != 3:
        raise ValueError(f"Unsupported number of image dimensions: {img_file}")
    if not ignore_dtype:
        img = img.astype(np.float32)
    return img


def write_image(
    img: np.ndarray,
    img_file: Union[str, PathLike],
    ignore_dtype: bool = False,
) -> Path:
    img_file = Path(img_file).with_suffix(".tiff")
    tifffile.imwrite(
        img_file,
        data=img,
        dtype=np.float32 if not ignore_dtype else None,
        imagej=True,
    )
    return img_file


def list_masks(mask_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(mask_dir).rglob("*.tiff"))


def read_mask(mask_file: Union[str, PathLike]) -> np.ndarray:
    mask_file = Path(mask_file).with_suffix(".tiff")
    mask = tifffile.imread(mask_file).astype(np.uint16)
    while mask.ndim > 2 and mask.shape[0] == 1:
        mask = mask.sqeeze(axis=0)
    while mask.ndim > 2 and mask.shape[-1] == 1:
        mask = mask.sqeeze(axis=mask.ndim - 1)
    if mask.ndim != 2:
        raise ValueError(f"Unsupported number of mask dimensions: {mask_file}")
    return mask


def write_mask(mask: np.ndarray, mask_file: Union[str, PathLike]) -> Path:
    mask_file = Path(mask_file).with_suffix(".tiff")
    tifffile.imwrite(mask_file, data=mask, dtype=np.uint16)
    return mask_file


def list_data(data_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(data_dir).rglob("*.csv"))


def read_data(
    data_file: Union[str, PathLike],
    combined: bool = False,
) -> pd.DataFrame:
    return pd.read_csv(
        Path(data_file).with_suffix(".csv"),
        index_col=["Image", "Object"] if combined else "Object",
    )


def write_data(
    df: pd.DataFrame,
    data_file: Union[str, PathLike],
    combined: bool = False,
    copy: bool = False,
) -> Path:
    if copy:
        df = df.reset_index()
    else:
        df.reset_index(inplace=True)
    data_file = Path(data_file).with_suffix(".csv")
    df.to_csv(data_file, index=False)
    return data_file


def list_distances(dists_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(dists_dir).rglob("*.csv"))


def read_distances(dists_file: Union[str, PathLike]) -> pd.DataFrame:
    dists_file = Path(dists_file).with_suffix(".csv")
    df = pd.read_csv(dists_file, index_col=0)
    df.index.name = "Object"
    df.index = df.index.astype(np.uint16)
    df.columns.name = "Object"
    df.columns = df.columns.astype(np.uint16)
    return df


def write_distances(
    df: pd.DataFrame,
    dists_file: Union[str, PathLike],
    copy: bool = False,
) -> Path:
    if copy:
        df = df.copy()
    df.index.name = "Object"
    df.index = df.index.astype(np.uint16)
    df.columns.name = "Object"
    df.columns = df.columns.astype(np.uint16)
    dists_file = Path(dists_file).with_suffix(".csv")
    df.to_csv(dists_file)
    return dists_file


def list_graphs(graph_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(graph_dir).rglob("*.csv"))


def read_graph(graph_file: Union[str, PathLike]) -> pd.DataFrame:
    return pd.read_csv(
        Path(graph_file).with_suffix(".csv"),
        usecols=["Object1", "Object2"],
        dtype=np.uint16,
    )


def write_graph(
    df: pd.DataFrame,
    graph_file: Union[str, PathLike],
) -> Path:
    df = df.loc[:, ["Object1", "Object2"]].astype(np.uint16)
    graph_file = Path(graph_file).with_suffix(".csv")
    df.to_csv(graph_file, index=False)
    return graph_file
