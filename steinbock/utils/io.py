import numpy as np
import pandas as pd
import tifffile
import xarray as xr

from imctoolkit import SpatialCellGraph
from os import PathLike
from typing import Union

panel_number_col = "channel"
panel_name_col = "name"


def read_panel(panel_file: Union[str, PathLike]) -> pd.DataFrame:
    panel = pd.read_csv(panel_file)
    if panel_number_col not in panel:
        raise ValueError(f"Missing {panel_number_col} in panel {panel_file}")
    if panel_name_col not in panel:
        raise ValueError(f"Missing {panel_name_col} in panel {panel_file}")
    if (
        panel[panel_number_col].isna().any()
        or panel[panel_number_col].min() != 1
        or panel[panel_number_col].max() != len(panel.index)
        or not panel[panel_number_col].is_unique
    ):
        raise ValueError(
            "Channel number is not one-based, incomplete, "
            f"or contains duplicates in panel {panel_file}"
        )
    if panel[panel_name_col].isna().any():
        raise ValueError(f"Incomplete channel names in panel {panel_file}")
    if "keep" in panel:
        panel = panel.loc[panel["keep"].astype(bool), :].drop(columns="keep")
    panel[panel_number_col] = panel[panel_number_col].astype(int)
    panel.sort_values(panel_number_col, inplace=True)
    return panel


def read_image(img_file: Union[str, PathLike]) -> np.ndarray:
    img = tifffile.imread(img_file).squeeze()
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    elif img.ndim != 3:
        raise ValueError(f"Unsupported number of iamge dimensions: {img_file}")
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
    return pd.read_csv(cell_data_file)


def write_cell_data(
    cell_data: pd.DataFrame,
    cell_data_file: Union[str, PathLike],
):
    cell_data.to_csv(cell_data_file)


def read_cell_dist(cell_dist_file: Union[str, PathLike]) -> xr.DataArray:
    return xr.open_dataarray(cell_dist_file)


def write_cell_dist(
    cell_dist: xr.DataArray,
    cell_dist_file: Union[str, PathLike],
):
    cell_dist.to_netcdf(cell_dist_file)


def write_cell_graph(
    cell_graph: SpatialCellGraph,
    cell_graph_file: Union[str, PathLike],
):
    g = cell_graph.to_igraph()
    g.write_graphml(cell_graph_file)
