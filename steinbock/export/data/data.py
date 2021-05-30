import pandas as pd

from anndata import AnnData
from os import PathLike
from pathlib import Path
from typing import Generator, Optional, Sequence, Tuple, Union

from steinbock import io


def collect_data_from_disk(
    data_dirs: Sequence[Union[str, PathLike]],
) -> pd.DataFrame:
    img_file_names = []
    merged_data_objs = []
    data_file_groups = (io.list_data_files(data_dir) for data_dir in data_dirs)
    for data_files in zip(*data_file_groups):
        img_file_name = Path(data_files[0]).with_suffix(".tiff").name
        merged_data = io.read_data(data_files[0])
        for data_file in data_files[1:]:
            merged_data = pd.merge(
                merged_data,
                io.read_data(data_file),
                left_index=True,
                right_index=True,
            )
        img_file_names.append(img_file_name)
        merged_data_objs.append(merged_data)
    return pd.concat(
        merged_data_objs,
        keys=img_file_names,
        names=["Image", "Object"]
    )


def to_anndata(
    intensities: pd.DataFrame,
    regionprops: Optional[pd.DataFrame] = None,
) -> AnnData:
    return AnnData(X=intensities, obs=regionprops)


def to_anndata_from_disk(
    intensities_files: Sequence[Union[str, PathLike]],
    regionprops_files: Optional[Sequence[Union[str, PathLike]]] = None,
) -> Generator[Tuple[Path, Optional[Path], AnnData], None, None]:
    for i, intensities_data_file in enumerate(intensities_files):
        intensities = io.read_data(intensities_data_file)
        regionprops = None
        regionprops_file = None
        if regionprops_files is not None:
            regionprops_file = regionprops_files[i]
            regionprops = io.read_data(regionprops_file)
        ad = to_anndata(intensities, regionprops=regionprops)
        yield intensities_data_file, regionprops_file, ad
        del intensities, regionprops, ad
