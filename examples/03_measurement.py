# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
import numpy as np
import pandas as pd

from pathlib import Path

from steinbock import io
from steinbock.measurement import intensities, regionprops, neighbors

import helpers

# %% [markdown]
# # Measurement
#
# This notebook is the third and last in the image preprocessing pipeline and should be run after the `segmentation` notebook.
#
# Here, we will export single cell measurements from multichannel image stacks using the cell segmentation masks that were created in the previous notebook (`segmentation`).
#
# Before running your own script please check the [steinbock documentation](https://bodenmillergroup.github.io/steinbock).

# %% [markdown]
# ## Settings
#
# ### Input and output directories
# Use the same working directory as in the `preprocessing` notebook (by default, the `examples` folder).
#
# Folder structure:

# %% [raw]
# steinbock data/working directory  
# ├── raw   
# |    └──── *.zip (raw data)
# ├── panel.csv (user-provided, when starting from raw data) 
# ├── img (created by this script)  
# ├── segstacks (created by this script)  
# ├── masks (created by this script)  
# ├── intensities (created by this script)  
# ├── regionprops (created by this script)  
# └── neighbors (created by this script)  

# %%
working_dir = Path(".")

# Output directories
img_dir = working_dir / "img"
masks_dir = working_dir / "masks"
intensities_dir = working_dir / "intensities"
regionprops_dir = working_dir / "regionprops"
neighbors_dir = working_dir / "neighbors"

# Create directories (if they do not already exist)
img_dir.mkdir(exist_ok=True)
masks_dir.mkdir(exist_ok=True)
intensities_dir.mkdir(exist_ok=True)
regionprops_dir.mkdir(exist_ok=True)
neighbors_dir.mkdir(exist_ok=True)

# %% [markdown]
# ### Import the antibody panel

# %%
panel_file = working_dir / "panel.csv"
panel = io.read_panel(panel_file)
panel.head()

# %% [markdown]
# ### Segmentation type
#
# Define the segmentation type to use for data extraction: either `nuclear` or `whole-cell`. Corresponding masks must have been generated in the previous notebook (`segmentation`).

# %%
segmentation_type = "nuclear"

# Define the masks output directory
masks_subdir = masks_dir / segmentation_type
masks_subdir.mkdir(exist_ok=True, parents=True)

# %% [markdown]
# ## Measure cell intensities per channel
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/measurement/#object-intensities

# %%
for img_path, mask_path, intens in intensities.try_measure_intensities_from_disk(
    img_files = io.list_image_files(img_dir),
    mask_files = io.list_image_files(masks_subdir),
    channel_names = panel["name"],
    intensity_aggregation = intensities.IntensityAggregation.MEAN
):
    intensities_file = Path(intensities_dir) / f"{img_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(intens, intensities_file)

# %% [markdown]
# ## Measure cell spatial properties
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/measurement/#region-properties
#
# ### List properties to measure
#
# For a full list of measurable properties, refer to https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.regionprops

# %%
skimage_regionprops = [
        "area",
        "centroid",
        "major_axis_length",
        "minor_axis_length",
        "eccentricity",
    ]

# %% [markdown]
# ### Measure region properties

# %%
for img_path, mask_path, region_props in regionprops.try_measure_regionprops_from_disk(
    img_files = io.list_image_files(img_dir),
    mask_files = io.list_image_files(masks_subdir),
    skimage_regionprops = skimage_regionprops
):
    
    regionprops_file = Path(regionprops_dir) / f"{img_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(region_props, regionprops_file)

# %% [markdown]
# ## Measure cell neighbors
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/measurement/#object-neighbors
#
# ### Settings
#
# *Neighborhood types:*
# + `NeighborhoodType.CENTROID_DISTANCE`
# + `NeighborhoodType.EUCLIDEAN_BORDER_DISTANCE`
# + `NeighborhoodType.EUCLIDEAN_PIXEL_EXPANSION`
#
# *Thresholding:*
# + `dmax` (max distance between centroids)
# + `kmax` (k-nearest neighbors)

# %%
neighborhood_type = neighbors.NeighborhoodType.CENTROID_DISTANCE
dmax = 15
kmax = 5

# %% [markdown]
# ### Measure cell neighbors

# %%
for mask_path, neighb in neighbors.try_measure_neighbors_from_disk(
    mask_files = io.list_image_files(masks_subdir),
    neighborhood_type = neighborhood_type,
    metric = "euclidean",
    dmax = dmax,
    kmax = kmax
):
    neighb_file = Path(neighbors_dir) / f"{mask_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(neighb, neighb_file, index=False)

# %%
# !conda list
