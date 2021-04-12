import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from scipy.ndimage import distance_transform_edt
from scipy.spatial import distance
from skimage import measure
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


def measure_cell_centroid_dists(
    mask_files: Sequence[Union[str, PathLike]],
    metric: str,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for mask_file in mask_files:
        mask = io.read_mask(mask_file)
        properties = measure.regionprops(mask)
        cell_ids = np.array([p.label for p in properties])
        cell_centroids = np.array([p.centroid for p in properties])
        cell_dists_data = distance.pdist(cell_centroids, metric=metric)
        cell_dists_data = distance.squareform(cell_dists_data, checks=False)
        cell_dists = pd.DataFrame(
            data=cell_dists_data,
            index=pd.Index(cell_ids, dtype=np.uint16, name="Cell"),
            columns=pd.Index(cell_ids, dtype=np.uint16, name="Cell"),
        )
        yield Path(mask_file), cell_dists


def measure_euclidean_cell_border_dists(
    mask_files: Sequence[Union[str, PathLike]],
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for mask_file in mask_files:
        mask = io.read_mask(mask_file)
        cell_ids = np.unique(mask[mask != 0])
        cell_dists_data = np.zeros((len(cell_ids), len(cell_ids)))
        for i, cell_id in enumerate(cell_ids):
            distances = distance_transform_edt(mask != cell_id)
            cell_dists_data[i, i + 1 :] = cell_dists_data[i + 1 :, i] = [
                np.amin(distances[mask == neighbor_cell_id])
                for neighbor_cell_id in cell_ids[i + 1 :]
            ]
        cell_dists = pd.DataFrame(
            data=cell_dists_data,
            index=pd.Index(cell_ids, dtype=np.uint16, name="Cell"),
            columns=pd.Index(cell_ids, dtype=np.uint16, name="Cell"),
        )
        yield Path(mask_file), cell_dists
