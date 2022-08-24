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
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tifffile
import xtiff

from deepcell.applications import Mesmer
from matplotlib.colors import ListedColormap
from pathlib import Path
from skimage import exposure
from skimage.segmentation import expand_labels
import sklearn

from steinbock import io
from steinbock.preprocessing import imc
from steinbock.segmentation import deepcell
from steinbock.measurement import intensities, regionprops, neighbors

import helpers

# %% [markdown]
# # Multiplex images preprocessing pipeline
#
# This pipeline will run image segmentation within the steinbock workframe. It can be applied to any multiplex image stacks. 
#
# Before running your own script please check the [steinbock documentation](https://bodenmillergroup.github.io/steinbock).
#
# *Installation*  
# To install the required python environment, follow the instructions here: https://bodenmillergroup.github.io/steinbock/latest/install-python/

# %% [markdown]
# ## Settings
#
# Example data can be downloaded using the `download_examples.ipynb` script.
#
# ### Input and output directories
#
# Folder structure:

# %% [raw]
# steinbock data/working directory  
# ├── panel.csv (user-provided)  
# ├── raw (*.tiff stacks, user-provided)
# ├── img (*.tiff image stacks, user-provided or generated from stacks in "raw")
# ├── masks (created by this script)  
# ├── intensities (created by this script)  
# ├── regionprops (created by this script)  
# └── neighbors (created by this script)  

# %%
base_dir = Path(".")

# Path to single tiff images
raw_dir = base_dir / "raw"

# Paths to tiff stacks
img_dir = base_dir / "img"

# Output directories
masks_dir = base_dir / "masks"
segstack_dir = base_dir / "segstacks"
intensities_dir = base_dir / "intensities"
regionprops_dir = base_dir / "regionprops"
neighbors_dir = base_dir / "neighbors"

# Create directories (if they do not already exist)
raw_dir.mkdir(exist_ok=True)
img_dir.mkdir(exist_ok=True)
masks_dir.mkdir(exist_ok=True)
segstack_dir.mkdir(exist_ok=True)
intensities_dir.mkdir(exist_ok=True)
regionprops_dir.mkdir(exist_ok=True)
neighbors_dir.mkdir(exist_ok=True)

# %% [markdown]
# ### Antibody panel
# The antibody panel should meet the steinbock format: https://bodenmillergroup.github.io/steinbock/latest/file-types/#panel  
#
# Customized panels should contain the following columns:
# + `channel`: unique channel id, typically metal and isotope mass (e.g. `Ir191`) or fluorophore.
# + `name`: unique channel name.
# + `deepcell`: channels to use for segmentation (1=nuclear, 2=membrane, empty/NaN=ignored).
# + `keep`: *(optional)* 1 for channels to preprocess, 0 for channels to ignore

# %%
panel = pd.read_csv(base_dir / "panel.csv")

if "keep" in panel.columns:
    panel = panel[panel["keep"]==1]

nb_of_channels = len(panel)
panel.head()

# %% [markdown]
# ### Re-shape `.tiff` stacks
#
# The multichannel image stacks provided by the user in the `raw` folder is reshaped as "CYX" (channel, height, width). Other dimensions are ignored: for a time series for instance, please provide one stack per time point.
#
# Alternately, the user can provide single-channel `tiff` files that will be converted to multichannel stacks. For this, the `generate_from_single_tiffs` variable has to be set to `True` and all images belonging to the same stack should start with the same prefix.
#
# If the `raw` folder is empty, it is assumed that  properly shaped stacks are directly provided by the user in the `img` folder.

# %%
generate_from_single_tiffs = True

raw_tiffs = sorted(Path(raw_dir).glob("*.tiff"))

# %%
if raw_tiffs and generate_from_single_tiffs:
    from itertools import cycle
    from os.path import commonprefix
    
    for i, j in zip(range(len(raw_tiffs)),
                    cycle(range(nb_of_channels))):
        cur_img = tifffile.imread(raw_tiffs[i])
        cur_img = np.expand_dims(cur_img, axis=0)
        
        if (j == 0):
            img = cur_img
            img_names = []
        else:
            img = np.concatenate((img, cur_img), axis = 0)
            
        img_names.append(raw_tiffs[i].name)
        
        if (j == (nb_of_channels-1)):
            img_file = img_dir / (commonprefix(img_names) + ".tiff")
            tifffile.imwrite(img_file, img,
                             photometric='minisblack',
                             metadata={'axes': 'CYX'}) 

# %%
if raw_tiffs and not generate_from_single_tiffs:
    for raw_tiff in raw_tiffs:
        with tifffile.TiffFile(raw_tiff) as tif:
            volume = tif.asarray()
            axes = tif.series[0].axes
            imagej_metadata = tif.imagej_metadata
            
            img_file = img_dir / raw_tiff.name
            tifffile.imwrite(img_file, volume,
                             photometric='minisblack',
                             metadata={'axes': 'CYX'}) 

# %% [markdown]
# ## Cell segmentation
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/segmentation/#deepcell  

# %% [markdown]
# ### Prepare segmentation stacks
#
# Segmentation stacks are generated by aggregating the channels selcted in `panel.csv` in the column `deepcell`. 
# Cell segmentation requires to construct as 2-channel images with the following structure:
# + Channel 1 = nuclear channels
# + Channel 2 = cytoplasmic/membranous channels.
#
# For channel-wise normalization, zscore and min-max methods are available.  
# In addition, different functions can be used to aggregate channels. Default: `np.mean`, for other options, see https://numpy.org/doc/stable/reference/routines.statistics.html#averages-and-variances.

# %%
# Define image preprocessing options
aggr_func = np.sum

# Define channels to use for segmentation (from the panel file)
channel_groups = panel["deepcell"].values
channel_groups = np.where(channel_groups == 0, np.nan, channel_groups) # make sure unselected chanels are set to "nan"

# %% [markdown]
# #### Generate segmentation stacks

# %%
for img_path in sorted(Path(img_dir).glob("*.tiff")):
    img = tifffile.imread(img_path).astype("uint8")
    
    img = np.moveaxis(img, -1, 0)
    img = exposure.equalize_adapthist(img, clip_limit=0.03)
    img = np.moveaxis(img, 0, -1)
    
    if channel_groups is not None:
        img = helpers.segstack_channels(img, channel_groups, aggr_func)
    
    img_file = Path(segstack_dir) / img_path.name
    tifffile.imwrite(img_file, (img*255).astype("uint8"))

# %% [markdown]
# #### Check segmentation stacks

# %%
segstacks = sorted(Path(segstack_dir).glob("*.tiff"))
rng = np.random.default_rng()
ix = rng.choice(len(segstacks))

fig, ax = plt.subplots(1, 2, figsize=(30, 30))

im = io.read_image(segstacks[ix])
ax[0].imshow(im[0,:,:], vmin=0, vmax=250) # adjust vmax if needed (lower value = higher intensity)
ax[0].set_title(segstacks[ix].stem + ": nuclei")

im = io.read_image(segstacks[ix])
ax[1].imshow(im[1,:,:], vmin=0, vmax=200) # adjust vmax if needed (lower value = higher intensity)
ax[1].set_title(segstacks[ix].stem + ": membrane")

# %% [markdown]
# ### Segment cells
#
# `segmentation_type` should be `whole-cell` or `nuclear`.
#
# Several post-processing arguments can be passed to the deepcell application, the defaults are selected below. Cell labels can also be expanded by defining an `expansion_distance` (mostly useful for nuclear segmentation).
#
# - `maxima_threshold`: set lower if cells are missing (default=0.6).
# - `maxima_smooth`: (default=0).
# - `interior_threshold`: set higher if you your nuclei are too large (default=0.6).
# - `interior_smooth`: larger values give rounder cells (default=2).
# - `small_objects_threshold`: depends on the image resolution (default=50).
# - `fill_holes_threshold`: (default=10).  
# - `radius`: (default=2).

# %%
# Segmentation type
segmentation_type = "nuclear"

# Label expansion (in pixels, 0 = no expansion)
expansion_distance = 1

# Resolution (microns per pixel)
mpp_resolution = 1.3

# %%
# Post-processing arguments for nuclear segmentation
kwargs_nuclear =  {
    'maxima_threshold': 0.1,
    'maxima_smooth': 0,
    'interior_threshold': 0.2,
    'interior_smooth': 2,
    'small_objects_threshold': 15,
    'fill_holes_threshold': 15,
    'radius': 2
}

# %%
# Post-processing arguments for whole-cell segmentation
kwargs_whole_cell =  { #these are valid if you select segmentation type = "whole-cell", I don't recommend
    'maxima_threshold': 0.075,
    'maxima_smooth': 0,
    'interior_threshold': 0.2,
    'interior_smooth': 2,
    'small_objects_threshold': 15,
    'fill_holes_threshold': 15,
    'radius': 2
}

# %%
app = Mesmer()

for stack in segstacks:
    img = io.read_image(stack)
    img = np.moveaxis(img, 0, 2)
    img = np.expand_dims(img.data, 0)
    
    mask = app.predict(
        img, image_mpp=mpp_resolution,
        compartment=segmentation_type,
        postprocess_kwargs_whole_cell=kwargs_whole_cell,
        postprocess_kwargs_nuclear=kwargs_nuclear
    )
    
    helpers.save_masks(
        mask, masks_dir, stack.name,
        segmentation_type, expansion_distance
    )

# %% [markdown]
# #### Check segmentation
#
# Adjust the image intensity by modifiying the `max_intensity` variable.  
# For higher magnification images, adjust the coordinates and dimension if needed.

# %%
# List masks
masks_subdir = masks_dir / segmentation_type
masks = sorted(Path(masks_subdir).glob("*.tiff"))

# Define instensity value for images
max_intensity = 250 # vmax: lower values = higher intensity

# Select a random image
ix = rng.choice(len(masks))
#ix = 1
fig, ax = plt.subplots(2, 2, figsize=(30, 30))

# Display image and mask
img = io.read_image(segstacks[ix])
ax[0,0].imshow(img[0,:,:], vmax=max_intensity)
ax[0,0].set_title(segstacks[ix].stem + ": nuclei")

mask = io.read_image(masks[ix])
cmap = ListedColormap(np.random.rand(10**6,3))
cmap.colors[0]=[1,1,1]
ax[0,1].imshow(mask[0,:,:], cmap=cmap)
ax[0,1].set_title(masks[ix].stem +": mask")

## Higher magnification (change coordinates and dimensions if needed)
xstart = 100
ystart = 100
dim = 200

ax[1,0].imshow(img[0,:,:], vmin=0, vmax=max_intensity) 
ax[1,0].set_title(segstacks[ix].stem + ": nuclei")
ax[1,0].set_xlim([xstart, xstart+dim])
ax[1,0].set_ylim([ystart, ystart+dim])

ax[1,1].imshow(mask[0,:,:], cmap=cmap)
ax[1,1].set_title(masks[ix].stem +": mask")
ax[1,1].set_xlim([xstart, xstart+dim])
ax[1,1].set_ylim([ystart, ystart+dim])

# %% [markdown]
# ## Measure cells
#
# ### Measure cell intensities per channel
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/measurement/#object-intensities

# %%
channel_names = panel["name"]
intensity_aggregation = intensities.IntensityAggregation.MEAN
    
for img_path in io.list_image_files(img_dir):
    img = tifffile.imread(img_path).astype("uint8")
    mask = tifffile.imread(masks_subdir / img_path.name, squeeze=True)
    
    intens = intensities.measure_intensites(img, mask, channel_names, intensity_aggregation)
    
    intensities_file = Path(intensities_dir) / f"{mask_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(intens, intensities_file)

# %% [markdown]
# ### Measure cell spatial properties
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/measurement/#region-properties
#
# #### List properties to measure
#
# For a full list of measurable properties, refer to https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.regionprops

# %%
skimage_regionprops = [
        "area",
        "centroid",
        #"major_axis_length",
        #"minor_axis_length",
        #"eccentricity",
    ]

# %% [markdown]
# #### Measure region props

# %%
for img_path in io.list_image_files(img_dir):
    img = tifffile.imread(img_path).astype("uint8")
    mask_path = masks_subdir / img_path.name
    mask = tifffile.imread(mask_path, squeeze=True)
    channel_names = panel["name"]
    intensity_aggregation = intensities.IntensityAggregation.MEAN
    
    intens = intensities.measure_intensites(img, mask, channel_names, intensity_aggregation)
    
    intensities_file = Path(intensities_dir) / f"{mask_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(intens, intensities_file)

# %% [markdown]
# ### Measure cell neighbors
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/measurement/#object-neighbors
#
# #### Settings
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
dmax = 20
kmax = 50

# %% [markdown]
# #### Measure cell neighbors
#
# Warning: time-consuming step for large images.

# %%
for img_path in io.list_image_files(img_dir):
    mask = tifffile.imread(masks_subdir / img_path.name, squeeze=True)
    
    neighb = neighbors.measure_neighbors(
        mask,
        neighborhood_type = neighborhood_type,
        metric = "euclidean",
        dmax = dmax,
        kmax = kmax
    )
    
    neighb_file = Path(neighbors_dir) / f"{mask_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(neighb, neighb_file, index=False)

# %%
# !conda list
