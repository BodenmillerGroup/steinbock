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


def read_image(img_file: Union[str, PathLike]) -> np.ndarray:
    img_file = Path(img_file).with_suffix(".tiff")
    img = tifffile.imread(img_file).squeeze().astype(np.float32)
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    elif img.ndim != 3:
        raise ValueError(f"Unsupported number of image dimensions: {img_file}")
    return img


def write_image(img: np.ndarray, img_file: Union[str, PathLike]) -> Path:
    img_file = Path(img_file).with_suffix(".tiff")
    tifffile.imwrite(img_file, data=img, dtype=np.float32, imagej=True)
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
    tifffile.imwrite(mask_file, data=mask, dtype=np.uint16, imagej=True)
    return mask_file


def list_cell_data(cell_data_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(cell_data_dir).rglob("*.csv"))


def read_cell_data(cell_data_file: Union[str, PathLike]) -> pd.DataFrame:
    cell_data_file = Path(cell_data_file).with_suffix(".csv")
    cell_data = pd.read_csv(cell_data_file, index_col=0)
    cell_data.index.name = "Cell"
    cell_data.columns.name = "Feature"
    return cell_data


def write_cell_data(
    cell_data: pd.DataFrame,
    cell_data_file: Union[str, PathLike],
) -> Path:
    cell_data.index.name = "Cell"
    cell_data.columns.name = "Feature"
    cell_data_file = Path(cell_data_file).with_suffix(".csv")
    cell_data.to_csv(cell_data_file)
    return cell_data_file


def list_cell_dists(cell_dists_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(cell_dists_dir).rglob("*.csv"))


def read_cell_dists(cell_dists_file: Union[str, PathLike]) -> pd.DataFrame:
    cell_dists_file = Path(cell_dists_file).with_suffix(".csv")
    cell_dists = pd.read_csv(cell_dists_file, index_col=0)
    cell_dists.index.name = "Cell"
    cell_dists.index = cell_dists.index.astype(np.uint16)
    cell_dists.columns.name = "Cell"
    cell_dists.columns = cell_dists.columns.astype(np.uint16)
    return cell_dists


def write_cell_dists(
    cell_dists: pd.DataFrame,
    cell_dists_file: Union[str, PathLike],
) -> Path:
    cell_dists.index.name = "Cell"
    cell_dists.index = cell_dists.index.astype(np.uint16)
    cell_dists.columns.name = "Cell"
    cell_dists.columns = cell_dists.columns.astype(np.uint16)
    cell_dists_file = Path(cell_dists_file).with_suffix(".csv")
    cell_dists.to_csv(cell_dists_file)
    return cell_dists_file


def list_cell_graphs(cell_graph_dir: Union[str, PathLike]) -> List[Path]:
    return sorted(Path(cell_graph_dir).rglob("*.csv"))


def read_cell_graph(cell_graph_file: Union[str, PathLike]) -> pd.DataFrame:
    cell_graph_file = Path(cell_graph_file).with_suffix(".csv")
    return pd.read_csv(
        cell_graph_file,
        usecols=["Cell1", "Cell2"],
        dtype=np.uint16,
    )


def write_cell_graph(
    cell_graph: pd.DataFrame,
    cell_graph_file: Union[str, PathLike],
) -> Path:
    cell_graph = cell_graph.astype(np.uint16)
    cell_graph.columns = ["Cell1", "Cell2"]
    cell_graph.reset_index(drop=True, inplace=True)
    cell_graph_file = Path(cell_graph_file).with_suffix(".csv")
    cell_graph.to_csv(cell_graph_file, index=False)
    return cell_graph_file
