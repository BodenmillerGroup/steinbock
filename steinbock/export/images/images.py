import numpy as np

from os import PathLike
from typing import Sequence, Union
from xtiff import to_tiff

from steinbock.version import version


def write_ome_tiff(
    img: np.ndarray,
    ome_file: Union[str, PathLike],
    channel_names: Sequence[str],
    **kwargs,
):
    if 'software' not in kwargs:
        kwargs['software'] = f"steinbock, version {version}"
    to_tiff(img, ome_file, channel_names=channel_names, **kwargs)
