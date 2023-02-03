import logging
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import Generator, Optional, Protocol, Sequence, Tuple, Union

import numpy as np

from .. import io
from ._segmentation import SteinbockSegmentationException

try:
    import cellpose.models

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
    model_name: str,
    img_files: Sequence[Union[str, PathLike]],
    channelwise_minmax: bool = False,
    channelwise_zscore: bool = False,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: AggregationFunction = np.mean,
    net_avg: bool = True,
    batch_size: int = 8,
    normalize: bool = True,
    diameter: Optional[int] = None,
    tile: bool = False,
    tile_overlap: float = 0.1,
    resample: bool = True,
    interp: bool = True,
    flow_threshold: float = 0.4,
    cellprob_threshold: float = 0.0,
    min_size: int = 15,
) -> Generator[Tuple[Path, np.ndarray, np.ndarray, np.ndarray, float], None, None]:
    model = cellpose.models.Cellpose(model_type=model_name, net_avg=net_avg)
    for img_file in img_files:
        try:
            img = create_segmentation_stack(
                io.read_image(img_file),
                channelwise_minmax=channelwise_minmax,
                channelwise_zscore=channelwise_zscore,
                channel_groups=channel_groups,
                aggr_func=aggr_func,
            )
            # channels: [cytoplasmic, nuclear]
            if img.shape[0] == 1:
                channels = [0, 0]  # grayscale image (cytoplasmic channel only)
            elif img.shape[0] == 2:
                channels = [2, 1]  # R=1 G=2 B=3 image (nuclear & cytoplasmic channels)
            else:
                raise SteinbockCellposeSegmentationException(
                    f"Invalid number of aggregated channels: "
                    f"expected 1 or 2, got {img.shape[0]}"
                )
            masks, flows, styles, diams = model.eval(
                [img],
                batch_size=batch_size,
                channels=channels,
                channel_axis=0,
                normalize=normalize,
                diameter=diameter,
                net_avg=net_avg,
                tile=tile,
                tile_overlap=tile_overlap,
                resample=resample,
                interp=interp,
                flow_threshold=flow_threshold,
                cellprob_threshold=cellprob_threshold,
                min_size=min_size,
                progress=False,
            )
            diam = diams if isinstance(diams, float) else diams[0]
            yield Path(img_file), masks[0], flows[0], styles[0], diam
            del img, masks, flows, styles, diams
        except Exception as e:
            logger.exception(f"Error segmenting objects in {img_file}: {e}")
