import numpy as np
import pandas as pd
import tifffile

from imctoolkit import SpatialCellGraph
from os import PathLike
from typing import Union

panel_name_col = "name"


def read_panel(panel_file: Union[str, PathLike]) -> pd.DataFrame:
    panel = pd.read_csv(panel_file)
    if panel_name_col not in panel:
        raise ValueError(f"Missing {panel_name_col} in panel {panel_file}")
    if panel[panel_name_col].isna().any():
        raise ValueError(f"Incomplete channel names in panel {panel_file}")
    return panel


def read_image(img_file: Union[str, PathLike]) -> np.ndarray:
    img = tifffile.imread(img_file).squeeze()
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    elif img.ndim != 3:
        raise ValueError(f"Unsupported number of image dimensions: {img_file}")
    return img


def write_image(img: np.ndarray, img_file: Union[str, PathLike]):
    tifffile.imwrite(img_file, data=img, dtype=np.float32, imagej=True)


def read_mask(mask_file: Union[str, PathLike]) -> np.ndarray:
    mask = tifffile.imread(mask_file).squeeze()
    if mask.ndim != 2:
        raise ValueError(f"Unsupported number of mask dimensions: {mask_file}")
    return mask


def write_mask(mask: np.ndarray, mask_file: Union[str, PathLike]):
    tifffile.imwrite(mask_file, data=mask, dtype=np.uint16, imagej=True)


def read_cell_data(cell_data_file: Union[str, PathLike]) -> pd.DataFrame:
    return pd.read_csv(cell_data_file, index_col=0)


def write_cell_data(
    cell_data: pd.DataFrame,
    cell_data_file: Union[str, PathLike],
):
    cell_data.to_csv(cell_data_file)


def read_cell_dists(cell_dists_file: Union[str, PathLike]) -> np.ndarray:
    return np.genfromtxt(cell_dists_file, delimiter=",")


def write_cell_dists(
    cell_dists: np.ndarray,
    cell_dists_file: Union[str, PathLike],
):
    np.savetxt(cell_dists_file, cell_dists, delimiter=",")


def write_graph(graph: SpatialCellGraph, graph_file: Union[str, PathLike]):
    g = graph.to_igraph()
    g.write_graphml(str(graph_file))
