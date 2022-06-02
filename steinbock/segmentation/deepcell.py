import logging
from enum import Enum
from functools import partial
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import numpy as np

from .. import io
from ._segmentation import SteinbockSegmentationException

if TYPE_CHECKING:
    from tensorflow.keras.models import Model  # type: ignore


logger = logging.getLogger(__name__)
deepcell_available = find_spec("deepcell") is not None


class SteinbockDeepcellSegmentationException(SteinbockSegmentationException):
    pass


def _mesmer_application(model=None):
    from deepcell.applications import Mesmer

    app = Mesmer(model=model)

    def predict(
        img: np.ndarray,
        *,
        pixel_size_um: Optional[float] = None,
        segmentation_type: Optional[str] = None,
        preprocess_kwargs: Optional[Mapping[str, Any]] = None,
        postprocess_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> np.ndarray:
        assert img.ndim == 3
        if pixel_size_um is None:
            raise SteinbockDeepcellSegmentationException("Unknown pixel size")
        if segmentation_type is None:
            raise SteinbockDeepcellSegmentationException("Unknown segmentation type")
        mask = app.predict(
            np.expand_dims(np.moveaxis(img, 0, -1), 0),
            batch_size=1,
            image_mpp=pixel_size_um,
            compartment=segmentation_type,
            preprocess_kwargs=preprocess_kwargs or {},
            postprocess_kwargs_whole_cell=postprocess_kwargs or {},
            postprocess_kwargs_nuclear=postprocess_kwargs or {},
        )[0, :, :, 0]
        assert mask.shape == img.shape[1:]
        return mask

    return app, predict


class Application(Enum):
    """"""

    MESMER = partial(_mesmer_application)


def try_segment_objects(
    img_files: Sequence[Union[str, PathLike]],
    application: Application,
    model: Optional["Model"] = None,
    channelwise_minmax: bool = False,
    channelwise_zscore: bool = False,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: Callable[[np.ndarray], np.ndarray] = np.mean,
    **predict_kwargs,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    app, predict = application.value(model=model)
    for img_file in img_files:
        try:
            img = io.read_image(img_file)
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
                img[channel_stds > 0] /= channel_stds[
                    channel_stds > 0, np.newaxis, np.newaxis
                ]
            if channel_groups is not None:
                img = np.stack(
                    [
                        aggr_func(img[channel_groups == channel_group], axis=0)
                        for channel_group in np.unique(channel_groups)
                        if not np.isnan(channel_group)
                    ]
                )
            mask = predict(img, **predict_kwargs)
            yield Path(img_file), mask
            del img, mask
        except:
            logger.exception(f"Error segmenting objects in {img_file}")
