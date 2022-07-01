# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.8
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import numpy as np
import pandas as pd
from os import PathLike
from pathlib import Path
from typing import List, Union
from zipfile import ZipFile

from steinbock import io
from steinbock.preprocessing import imc
from steinbock.segmentation import deepcell
from steinbock.measurement import intensities, regionprops, neighbors

# %% [markdown]
# # IMC preprocessing pipeline
#
# **steinbock:**  
# Documentation: https://bodenmillergroup.github.io/steinbock

# %% [markdown]
# ## Settings
#
# Example data can be downloaded using the `download_examples.ipynb` script.

# %% [markdown]
# ### Input and output directories

# %%
base_dir = Path("..")

# Paths to zipped acquisition files
raw_dir = base_dir / "raw"

# Output directories
img_dir = base_dir / "img"
masks_dir = base_dir / "masks"
segstack_dir = base_dir / "segstacks"
intensities_dir = base_dir / "intensities"
regionprops_dir = base_dir / "regionprops"
neighbors_dir = base_dir / "neighbors"

# %% [markdown]
# ## Extract images from `.mcd` files
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/preprocessing/#image-conversion

# %% [markdown]
# ### Prepare the panel
# #### Panel file and column names

# %%
# Path to panel file
panel_file = raw_dir / "panel.csv"

# Panel columns
panel_channel_col = "metal"
panel_name_col = "name"
panel_keep_col = "full"
panel_cellseg_col = "deepcell"

# %% [markdown]
# #### Import the panel

# %%
# Only needed when dealing with panel files from the old ImcSegmentationPipeline
imc_panel = imc.create_panel_from_imc_panel(panel_file)

# If directly providing a good panel, simply use
# imc_panel = pd.read_csv(panel_file)

imc_panel.head()


# %% [markdown]
# ### Unzip
#
# Unzip function

# %%
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


# %%
# Extract .mcd files
extract_zips(path=raw_dir, suffix=".mcd", dest=raw_dir)

# %%
# Extract .txt files
extract_zips(path=raw_dir, suffix=".txt", dest=raw_dir)

# %% [markdown]
# ### Convert to tiff
# #### Settings

# %%
# Value for hot pixel filtering
hpf = 50
channel_names = imc_panel['channel']

# List mcd and txt files
mcd_files = imc.list_mcd_files(raw_dir)
txt_files = imc.list_txt_files(raw_dir)

img_dir.mkdir(exist_ok=True)

# %% [markdown]
# #### Convert
#
# also save image metadata

# %%
for img in imc.try_preprocess_images_from_disk(
    mcd_files = mcd_files,
    txt_files = txt_files,
    hpf = hpf,
    channel_names = channel_names
):
    img_file = Path(img_dir) / f"{img[0].stem}.tiff"
    io.write_image(img[2], img_file)

# %% [markdown]
# ## Cell segmentation

# %% [markdown]
# ### Prepare segmentation stacks

# %%
channel_groups = imc_panel["deepcell"].values
channelwise_zscore = True
aggr_func = np.sum
segstack_dir.mkdir(exist_ok=True)

# Suffixes
deepcell_suffix = "_deepcell"
mask_suffix = "_mask"

# %%
for img_path in Path(img_dir).iterdir():
    img = io.read_image(img_path)
    
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
    img_file = Path(segstack_dir) / f"{img_path.stem + deepcell_suffix}.tiff"
    io.write_image(img, img_file)

# %% [markdown]
# ### Segment cells

# %%
segstacks = sorted(Path(segstack_dir).glob("*" + deepcell_suffix + ".tiff"))
masks_dir.mkdir(exist_ok=True)

# %%
for img_path, mask in deepcell.try_segment_objects(
    img_files=segstacks,
    application=deepcell.Application.MESMER,
    pixel_size_um=1.0,
    segmentation_type = "whole-cell"
):
    mask_file = Path(masks_dir) / f"{img_path.name.replace(deepcell_suffix, mask_suffix)}"
    io.write_mask(mask, mask_file)        

# %% [markdown]
# ## Measure cells
#
# #### Create output folders

# %%
intensities_dir.mkdir(exist_ok=True)
regionprops_dir.mkdir(exist_ok=True)
neighbors_dir.mkdir(exist_ok=True)

# %% [markdown]
# ### Measure cell intensities per channel

# %%
for img_path, mask_path, intens in intensities.try_measure_intensities_from_disk(
    img_files = io.list_image_files(img_dir),
    mask_files = io.list_image_files(masks_dir),
    channel_names = channel_names,
    intensity_aggregation = intensities.IntensityAggregation.MEAN
):
    intensities_file = Path(intensities_dir) / f"{img_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(intens, intensities_file)

# %% [markdown]
# ### Measure cell spatial properties
#
# #### List properties to measure

# %%
skimage_regionprops = [
        "area",
        "centroid",
        "major_axis_length",
        "minor_axis_length",
        "eccentricity",
    ]

# %% [markdown]
# #### Measure region props

# %%
for img_path, mask_path, region_props in regionprops.try_measure_regionprops_from_disk(
    img_files = io.list_image_files(img_dir),
    mask_files = io.list_image_files(masks_dir),
    skimage_regionprops = skimage_regionprops
):
    regionprops_file = Path(regionprops_dir) / f"{img_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(region_props, regionprops_file)

# %% [markdown]
# ### Measure cell neighbors
#
# #### Settings
#
# Choose dmax (max distance between centroids) and/or kmax (k-nearest neighbors)
# Neighborhood types:
# + NeighborhoodType.CENTROID_DISTANCE,
# + NeighborhoodType.EUCLIDEAN_BORDER_DISTANCE,
# + NeighborhoodType.EUCLIDEAN_PIXEL_EXPANSION,

# %%
neighborhood_type = neighbors.NeighborhoodType.CENTROID_DISTANCE
dmax = 15
kmax = 5

# %% [markdown]
# #### Measure cell neighbors

# %%
for mask_path, neighb in neighbors.try_measure_neighbors_from_disk(
    mask_files = io.list_image_files(masks_dir),
    neighborhood_type = neighborhood_type,
    metric = "euclidean",
    dmax = dmax,
    kmax = kmax
):
    neighb_file = Path(neighbors_dir) / f"{mask_path.name.replace(mask_suffix + '.tiff', '.csv')}"
    pd.DataFrame.to_csv(neighb, neighb_file)

# %%
# !conda list
