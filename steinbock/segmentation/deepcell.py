import numpy as np

from deepcell.applications import Mesmer
from enum import Enum
from os import PathLike
from pathlib import Path
from tensorflow.keras.models import Model
from typing import Generator, Optional, Sequence, Tuple, Union

from steinbock import io

panel_deepcell_col = "deepcell"


class Application(Enum):
    MESMER = "Mesmer"


def _mesmer_app(model=None):
    app = Mesmer(model=model)

    def predict(
        img: np.ndarray,
        *,
        pixel_size_um: Optional[float] = None,
        segmentation_type: Optional[str] = None,
        **kwargs,
    ) -> np.ndarray:
        assert img.ndim == 3
        if pixel_size_um is None:
            raise ValueError("Unknown pixel size")
        if segmentation_type is None:
            raise ValueError("Unknown segmentation type")
        return app.predict(
            np.expand_dims(img, 0),
            batch_size=1,
            image_mpp=pixel_size_um,
            compartment=segmentation_type,
            **kwargs,
        )[0]

    return app, predict


_apps = {
    Application.MESMER: _mesmer_app,
}


def segment_objects(
    img_files: Sequence[Union[str, PathLike]],
    application: Application,
    model: Optional[Model] = None,
    channelwise_minmax: bool = False,
    channelwise_zscore: bool = False,
    channel_groups: Optional[np.ndarray] = None,
    **predict_kwargs,
) -> Generator[Tuple[Path, np.ndarray], None, None]:
    app, predict = _apps[application](model=model)
    for img_file in img_files:
        img_file = Path(img_file)
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
            img = img = np.stack(
                [
                    np.nanmean(img[channel_groups == cg, :, :], axis=0)
                    for cg in np.unique(channel_groups)
                    if not np.isnan(cg)
                ],
            )
        mask = predict(img, **predict_kwargs)
        yield img_file, mask
