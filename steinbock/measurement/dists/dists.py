import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from scipy.ndimage import distance_transform_edt
from scipy.spatial.distance import pdist, squareform
from skimage.measure import regionprops
from typing import Generator, Sequence, Tuple, Union

from steinbock import io


def measure_centroid_dists(mask: np.ndarray, metric: str) -> pd.DataFrame:
    properties = regionprops(mask)
    object_ids = np.array([p.label for p in properties])
    object_centroids = np.array([p.centroid for p in properties])
    dists_data = squareform(
        pdist(object_centroids, metric=metric),
        checks=False,
    )
    return pd.DataFrame(
        data=dists_data,
        index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
        columns=pd.Index(object_ids, dtype=np.uint16, name="Object"),
    )


def measure_centroid_dists_from_disk(
    mask_files: Sequence[Union[str, PathLike]],
    metric: str,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for mask_file in mask_files:
        mask = io.read_mask(mask_file)
        dists = measure_centroid_dists(mask, metric)
        del mask
        yield Path(mask_file), dists
        del dists


def measure_euclidean_border_dists(mask: np.ndarray) -> pd.DataFrame:
    object_ids = np.unique(mask[mask != 0])
    dists_data = np.zeros((len(object_ids), len(object_ids)))
    for i, object_id in enumerate(object_ids):
        dist_img = distance_transform_edt(mask != object_id)
        dists_data[i, i + 1 :] = dists_data[i + 1 :, i] = [
            np.amin(dist_img[mask == neighbor_object_id])
            for neighbor_object_id in object_ids[i + 1 :]
        ]
    return pd.DataFrame(
        data=dists_data,
        index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
        columns=pd.Index(object_ids, dtype=np.uint16, name="Object"),
    )


def measure_euclidean_border_dists_from_disk(
    mask_files: Sequence[Union[str, PathLike]],
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for mask_file in mask_files:
        mask = io.read_mask(mask_file)
        dists = measure_euclidean_border_dists(mask)
        del mask
        yield Path(mask_file), dists
        del dists
