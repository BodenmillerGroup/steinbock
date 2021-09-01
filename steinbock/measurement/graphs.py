import numpy as np
import pandas as pd

from os import PathLike
from pathlib import Path
from scipy.ndimage import distance_transform_edt
from scipy.spatial.distance import pdist, squareform
from skimage.measure import regionprops
from typing import Generator, Optional, Sequence, Tuple, Union

from steinbock import io


def _to_triu_indices(k: np.ndarray, n: int) -> Tuple[np.ndarray, np.ndarray]:
    # https://stackoverflow.com/a/27088560 (optimized for numpy arrays)
    # Briefly, the formulas were derived using triangular numbers/roots
    i = n - 2 - np.floor((-8 * k + 4 * n * (n - 1) - 7) ** 0.5 / 2 - 0.5)
    j = k + i + 1 - (n * (n - 1) - (n - i) * (n - i - 1)) // 2
    return i.astype(int), j.astype(int)


def construct_centroid_dist_graph(
    mask: np.ndarray,
    metric: str,
    dmax: Optional[float] = None,
    kmax: Optional[int] = None,
) -> pd.DataFrame:
    props = regionprops(mask)
    labels = np.array([p.label for p in props])
    centroids = np.array([p.centroid for p in props])
    condensed_dists = pdist(centroids, metric=metric)
    if kmax is not None:
        k = min(kmax, len(props) - 1)
        dist_mat = squareform(condensed_dists, checks=False).astype(float)
        np.fill_diagonal(dist_mat, np.inf)
        knn_indices = np.argpartition(dist_mat, k - 1)[:, :k]
        if dmax is not None:
            knn_dists = np.take_along_axis(dist_mat, knn_indices, -1)
            indices1, indices2 = np.nonzero(knn_dists <= dmax)
            indices2 = knn_indices[(indices1, indices2)]
        else:
            indices1 = np.repeat(np.arange(len(props)), k)
            indices2 = np.ravel(knn_indices)
        distances = dist_mat[(indices1, indices2)]
    elif dmax is not None:
        (condensed_indices,) = np.nonzero(condensed_dists <= dmax)
        indices1, indices2 = _to_triu_indices(condensed_indices, len(props))
        distances = condensed_dists[condensed_indices]
        indices1, indices2, distances = (
            np.concatenate((indices1, indices2)),
            np.concatenate((indices2, indices1)),
            np.concatenate((distances, distances)),
        )
    else:
        raise ValueError("Specify either dmax or kmax (or both)")
    return pd.DataFrame(
        data={
            "Object": np.asarray(labels[indices1], dtype=io.mask_dtype),
            "Neighbor": np.asarray(labels[indices2], dtype=io.mask_dtype),
            "Distance": np.asarray(distances, dtype=float),
        }
    )


def construct_euclidean_border_dist_graph(
    mask: np.ndarray,
    dmax: Optional[float] = None,
    kmax: Optional[int] = None,
) -> pd.DataFrame:
    labels1 = []
    labels2 = []
    distances = []
    unique_labels = np.unique(mask)
    unique_labels = unique_labels[unique_labels != 0]
    for label in unique_labels:
        if dmax is not None:
            ys, xs = np.nonzero(mask == label)
            dmax_int = int(np.ceil(dmax))
            ymin, ymax = np.amin(ys) - dmax_int, np.amax(ys) + dmax_int
            xmin, xmax = np.amin(xs) - dmax_int, np.amax(xs) + dmax_int
            mask_or_patch = mask[
                max(0, ymin) : min(mask.shape[0], ymax),
                max(0, xmin) : min(mask.shape[1], xmax),
            ]
            neighbor_labels = np.unique(mask_or_patch)
            neighbor_labels = neighbor_labels[neighbor_labels != 0]
        else:
            mask_or_patch = mask
            neighbor_labels = unique_labels
        dists = distance_transform_edt(mask_or_patch != label)
        neighbor_labels = neighbor_labels[neighbor_labels != label]
        neighbor_dists = np.array(
            [
                np.amin(dists[mask_or_patch == neighbor_label])
                for neighbor_label in neighbor_labels
            ]
        )
        if dmax is not None:
            neighbor_labels = neighbor_labels[neighbor_dists <= dmax]
            neighbor_dists = neighbor_dists[neighbor_dists <= dmax]
        if kmax is not None and len(neighbor_labels) > kmax:
            knn_indices = np.argpartition(neighbor_dists, kmax - 1)[:kmax]
            neighbor_labels = neighbor_labels[knn_indices]
            neighbor_dists = neighbor_dists[knn_indices]
        labels1 += [label] * len(neighbor_labels)
        labels2 += neighbor_labels.tolist()
        distances += neighbor_dists.tolist()
    return pd.DataFrame(
        data={
            "Object": np.asarray(labels1, dtype=io.mask_dtype),
            "Neighbor": np.asarray(labels2, dtype=io.mask_dtype),
            "Distance": np.asarray(distances, dtype=float),
        }
    )


def expand_mask_euclidean(mask: np.ndarray, dmax: float) -> np.ndarray:
    dists, (i, j) = distance_transform_edt(mask == 0, return_indices=True)
    return np.where(dists <= dmax, mask[i, j], mask)


def construct_graph(
    mask: np.ndarray,
    graph_type: str,
    metric: Optional[str] = None,
    dmax: Optional[float] = None,
    kmax: Optional[int] = None,
) -> pd.DataFrame:
    if graph_type == "centroid":
        if metric is None:
            raise ValueError("Metric is required")
        return construct_centroid_dist_graph(
            mask, metric, dmax=dmax, kmax=kmax
        )
    if graph_type == "border":
        if metric not in (None, "euclidean"):
            raise ValueError("Metric has to be Euclidean for border distances")
        return construct_euclidean_border_dist_graph(
            mask, dmax=dmax, kmax=kmax
        )
    if graph_type == "expand":
        if metric not in (None, "euclidean"):
            raise ValueError("Metric has to be Euclidean for pixel expansion")
        if dmax is None:
            raise ValueError("Maximum distance required for pixel expansion")
        if kmax is not None:
            raise ValueError("Pixel expansion does not support kNN graphs")
        mask = expand_mask_euclidean(mask, dmax)
        return construct_euclidean_border_dist_graph(mask, dmax=1.0)
    raise ValueError(f"Unknown graph type: {graph_type}")


def construct_graphs_from_disk(
    mask_files: Sequence[Union[str, PathLike]],
    graph_type: str,
    metric: Optional[str] = None,
    dmax: Optional[float] = None,
    kmax: Optional[int] = None,
) -> Generator[Tuple[Path, pd.DataFrame], None, None]:
    for mask_file in mask_files:
        mask = io.read_mask(mask_file)
        graph = construct_graph(
            mask,
            graph_type,
            metric=metric,
            dmax=dmax,
            kmax=kmax,
        )
        yield Path(mask_file), graph
        del graph
