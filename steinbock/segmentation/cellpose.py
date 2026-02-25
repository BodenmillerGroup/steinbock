import logging
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import Generator, Optional, Protocol, Sequence, Tuple, Union

import numpy as np

from .. import io
from ._segmentation import SteinbockSegmentationException

try:
    from cellpose import models
    cellpose_available = True
except Exception:
    cellpose_available = False

logger = logging.getLogger(__name__)
cellpose_available = find_spec("cellpose") is not None


class SteinbockCellposeSegmentationException(SteinbockSegmentationException):
    pass


class AggregationFunction(Protocol):
    def __call__(self, img: np.ndarray, axis: Optional[int] = None) -> np.ndarray:
        ...


def create_segmentation_stack(
    img: np.ndarray,
    channelwise_minmax: bool = False,
    channelwise_zscore: bool = False,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: AggregationFunction = np.mean,
) -> np.ndarray:
    if channelwise_minmax:
        channel_mins = np.nanmin(img, axis=(1, 2))
        channel_maxs = np.nanmax(img, axis=(1, 2))
        channel_ranges = channel_maxs - channel_mins
        img -= channel_mins[:, np.newaxis, np.newaxis]
        img[channel_ranges > 0] /= channel_ranges[
            channel_ranges > 0, np.newaxis, np.newaxis
        ]
    if channelwise_zscore:
        channel_means = np.nanmean(img, axis=(1, 2))
        channel_stds = np.nanstd(img, axis=(1, 2))
        img -= channel_means[:, np.newaxis, np.newaxis]
        img[channel_stds > 0] /= channel_stds[channel_stds > 0, np.newaxis, np.newaxis]
    if channel_groups is not None:
        img = np.stack(
            [
                aggr_func(img[channel_groups == channel_group], axis=0)
                for channel_group in np.unique(channel_groups)
                if not np.isnan(channel_group)
            ]
        )
    return img


def try_segment_objects(
    img_files: Sequence[Union[str, PathLike]],
    channelwise_minmax: bool = False,
    channelwise_zscore: bool = False,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: AggregationFunction = np.mean,
    batch_size: int = 8,
    resample: bool = False,
    channel_axis: int = 0,
    normalize: bool = True,
    invert: bool = False,
    rescale: Optional[float] = None,
    diameter: Optional[int] = None,
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    min_size: int = 15,
    max_size_fraction: float = 0.4,
    niter: Optional[int] = None,
    augment: bool = False,
    tile_overlap: float = 0.1,
) -> Generator[Tuple[Path, np.ndarray, np.ndarray, np.ndarray], None, None]:
    model = models.CellposeModel(gpu=True) # cellpose checks for gpu availability internally, so we can just set gpu=True here.
    for img_file in img_files:
        try:
            img = create_segmentation_stack(
                io.read_image(img_file),
                channelwise_minmax=channelwise_minmax,
                channelwise_zscore=channelwise_zscore,
                channel_groups=channel_groups,
                aggr_func=aggr_func,
            )

            masks, flows, styles = model.eval(
                [img],
                batch_size=batch_size,
                resample=resample,
                channel_axis=channel_axis,
                normalize=normalize,
                invert=invert,
                rescale=rescale,
                diameter=diameter,
                flow_threshold=flow_threshold,
                cellprob_threshold=cellprob_threshold,
                min_size=min_size,
                max_size_fraction=max_size_fraction,
                niter=niter,
                augment=augment,
                tile_overlap=tile_overlap,
            )
            
            yield Path(img_file), masks[0], flows[0], styles[0]
            del img, masks, flows, styles
        except Exception as e:
            logger.exception(f"Error segmenting objects in {img_file}: {e}")
