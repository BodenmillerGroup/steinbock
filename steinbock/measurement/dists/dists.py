import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from scipy.ndimage import distance_transform_edt
from scipy.spatial import distance
from skimage.measure import regionprops
from typing import Generator, Sequence, Tuple, Union

from steinbock.utils import io


def measure_centroid_distances(
    mask_files: Sequence[Union[str, PathLike]],
    metric: str,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for mask_file in mask_files:
        mask = io.read_mask(mask_file)
        properties = regionprops(mask)
        object_ids = np.array([p.label for p in properties])
        object_centroids = np.array([p.centroid for p in properties])
        d_data = distance.squareform(
            distance.pdist(object_centroids, metric=metric),
            checks=False,
        )
        df = pd.DataFrame(
            data=d_data,
            index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
            columns=pd.Index(object_ids, dtype=np.uint16, name="Object"),
        )
        yield Path(mask_file), df
        del df


def measure_euclidean_border_distances(
    mask_files: Sequence[Union[str, PathLike]],
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for mask_file in mask_files:
        mask = io.read_mask(mask_file)
        object_ids = np.unique(mask[mask != 0])
        d_data = np.zeros((len(object_ids), len(object_ids)))
        for i, object_id in enumerate(object_ids):
            dist_img = distance_transform_edt(mask != object_id)
            d_data[i, i + 1 :] = d_data[i + 1 :, i] = [
                np.amin(dist_img[mask == neighbor_object_id])
                for neighbor_object_id in object_ids[i + 1 :]
            ]
        df = pd.DataFrame(
            data=d_data,
            index=pd.Index(object_ids, dtype=np.uint16, name="Object"),
            columns=pd.Index(object_ids, dtype=np.uint16, name="Object"),
        )
        yield Path(mask_file), df
        del df
