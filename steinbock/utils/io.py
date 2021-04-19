import numpy as np
import pandas as pd
import tifffile

from os import PathLike
from pathlib import Path
from typing import List, Union

panel_name_col = "name"


def read_panel(panel_file: Union[str, PathLike]) -> pd.DataFrame:
    panel_file = Path(panel_file).with_suffix(".csv")
    panel = pd.read_csv(panel_file)
    if panel_name_col not in panel:
        raise ValueError(f"Missing {panel_name_col} in panel {panel_file}")
    if panel[panel_name_col].isna().any():
        raise ValueError(f"Incomplete channel names in panel {panel_file}")
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
    img = tifffile.imread(img_file).squeeze()
    if not ignore_dtype:
        img = img.astype(np.float32)
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    elif img.ndim != 3:
        raise ValueError(f"Unsupported number of image dimensions: {img_file}")
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
    mask = tifffile.imread(mask_file).squeeze().astype(np.uint16)
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
    data: pd.DataFrame,
    data_file: Union[str, PathLike],
    combined: bool = False,
    copy: bool = False,
) -> Path:
    if copy:
        data = data.reset_index()
    else:
        data.reset_index(inplace=True)
    data_file = Path(data_file).with_suffix(".csv")
    data.to_csv(data_file, index=False)
    return data_file


def list_distances(distances_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(distances_dir).rglob("*.csv"))


def read_distances(distances_file: Union[str, PathLike]) -> pd.DataFrame:
    distances_file = Path(distances_file).with_suffix(".csv")
    d = pd.read_csv(distances_file, index_col=0)
    d.index.name = "Object"
    d.index = d.index.astype(np.uint16)
    d.columns.name = "Object"
    d.columns = d.columns.astype(np.uint16)
    return d


def write_distances(
    d: pd.DataFrame,
    distances_file: Union[str, PathLike],
    copy: bool = False,
) -> Path:
    if copy:
        d = d.copy()
    d.index.name = "Object"
    d.index = d.index.astype(np.uint16)
    d.columns.name = "Object"
    d.columns = d.columns.astype(np.uint16)
    distances_file = Path(distances_file).with_suffix(".csv")
    d.to_csv(distances_file)
    return distances_file


def list_graphs(graph_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(graph_dir).rglob("*.csv"))


def read_graph(graph_file: Union[str, PathLike]) -> pd.DataFrame:
    return pd.read_csv(
        Path(graph_file).with_suffix(".csv"),
        usecols=["Object1", "Object2"],
        dtype=np.uint16,
    )


def write_graph(
    g: pd.DataFrame,
    graph_file: Union[str, PathLike],
) -> Path:
    g = g[["Object1", "Object2"]].astype(np.uint16)
    graph_file = Path(graph_file).with_suffix(".csv")
    g.to_csv(g, index=False)
    return graph_file
