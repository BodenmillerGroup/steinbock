# Extract zips
import numpy as np
import pandas as pd

from os import PathLike
from typing import List, Union
from pathlib import Path
from zipfile import ZipFile

def extract_zips(
    path: Union[str, PathLike], suffix: str, dest: Union[str, PathLike]
) -> List[Path]:
    extracted_files = []
    for zip_file_path in Path(path).rglob("[!.]*.zip"):
        with ZipFile(zip_file_path) as zip_file:
            zip_infos = sorted(zip_file.infolist(), key=lambda x: x.filename)
            for zip_info in zip_infos:
                if not zip_info.is_dir() and zip_info.filename.endswith(suffix):
                    extracted_file = zip_file.extract(zip_info, path=dest)
                    extracted_files.append(Path(extracted_file))
    return extracted_files

# Extract metadata
def extract_metadata(
    img_file,
    mcd_file,
    img,
    acquisition,
    matched_txt,
    recovered
):
    recovery_file_name = None
    if matched_txt is not None:
        recovery_file_name = matched_txt.name

    image_info_row = {
        "image": img_file.name,
        "width_px": img.shape[2],
        "height_px": img.shape[1],
        "num_channels": img.shape[0],
        "source_file": mcd_file.name,
        "recovery_file": recovery_file_name,
        "recovered": recovered,
    }

    if acquisition is not None:
        image_info_row.update({
            "acquisition_id": acquisition.id,
            "acquisition_description": acquisition.description,
            "acquisition_start_x_um": (acquisition.roi_points_um[0][0]),
            "acquisition_start_y_um": (acquisition.roi_points_um[0][1]),
            "acquisition_end_x_um": (acquisition.roi_points_um[2][0]),
            "acquisition_end_y_um": (acquisition.roi_points_um[2][1]),
            "acquisition_width_um": acquisition.width_um,
            "acquisition_height_um": acquisition.height_um
        })

    image_info_data = pd.DataFrame.from_dict([image_info_row])
    return(image_info_data)
