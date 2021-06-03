import numpy as np

from enum import Enum
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import (
    Callable,
    Generator,
    Optional,
    Sequence,
    Tuple,
    TYPE_CHECKING,
    Union,
)

from steinbock import io

if TYPE_CHECKING:
    from tensorflow.keras.models import Model

deepcell_available = find_spec("deepcell") is not None


class DeepcellApplication(Enum):
    """"""

    MESMER = "Mesmer"


def _mesmer_app(model=None):
    from deepcell.applications import Mesmer

    app = Mesmer(model=model)

    def predict(
        img: np.ndarray,
        *,
        pixel_size_um: Optional[float] = None,
        segmentation_type: Optional[str] = None,
        **kwargs
    ) -> np.ndarray:
        assert img.ndim == 3
        if pixel_size_um is None:
            raise ValueError("Unknown pixel size")
        if segmentation_type is None:
            raise ValueError("Unknown segmentation type")
        mask = app.predict(
            np.expand_dims(np.moveaxis(img, 0, -1), 0),
            batch_size=1,
            image_mpp=pixel_size_um,
            compartment=segmentation_type,
            **kwargs
        )[0, :, :, 0]
        assert mask.shape == img.shape[1:]
        return mask

    return app, predict


_apps = {
    DeepcellApplication.MESMER: _mesmer_app,
}


def run_object_segmentation(
    img_files: Sequence[Union[str, PathLike]],
    application: DeepcellApplication,
    model: Optional["Model"] = None,
    channelwise_minmax: bool = False,
    channelwise_zscore: bool = False,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: Callable[[np.ndarray], np.ndarray] = np.nanmean,
    **predict_kwargs
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    app, predict = _apps[application](model=model)
    for img_file in img_files:
        img = io.read_image(img_file)
        if channelwise_minmax:
            channel_mins = np.nanmin(img, axis=(1, 2), keepdims=True)
            channel_maxs = np.nanmax(img, axis=(1, 2), keepdims=True)
            img = (img - channel_mins) / (channel_maxs - channel_mins)
        if channelwise_zscore:
            channel_means = np.nanmean(img, axis=(1, 2), keepdims=True)
            channel_stds = np.nanstd(img, axis=(1, 2), keepdims=True)
            img = (img - channel_means) / channel_stds
        if channel_groups is not None:

            def aggr(channel_img):
                return np.apply_along_axis(aggr_func, 0, channel_img)

            img = np.stack(
                [
                    aggr(img[channel_groups == channel_group])
                    for channel_group in np.unique(channel_groups)
                    if not np.isnan(channel_group)
                ]
            )
        mask = predict(img, **predict_kwargs)
        yield Path(img_file), mask
        del img, mask
