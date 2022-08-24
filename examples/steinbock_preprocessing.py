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
import xtiff

from deepcell.applications import Mesmer
from matplotlib.colors import ListedColormap
from pathlib import Path
from skimage.segmentation import expand_labels
from urllib import request
import sklearn

from steinbock import io
from steinbock.preprocessing import imc
from steinbock.segmentation import deepcell
from steinbock.measurement import intensities, regionprops, neighbors

import helpers

# %% [markdown]
# # IMC preprocessing pipeline
#
# This pipeline will extract image data from IMC aquisitions located in the `raw` folder and generate single cell data. Intermediary steps include the extraction of image stacks selected from the panel file as well as segmentation masks. The single cell data is extracted from the chanels selected in the panel.
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
base_dir = Path(".")

# Paths to zipped acquisition files
raw_dir = base_dir / "raw"

# Output directories
img_dir = base_dir / "img"
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
# ## Download IMC example data
# This section downloads IMC example raw data and the associated antibody panel file used for the experiment. The IMC raw data will be stored in the `raw` folder and the panel will be stored in the `examples` folder.  
# You can skip the following cell if you are processing your own data.

# %%
for example_file_name, example_file_url in [
    ("Patient1.zip", "https://zenodo.org/record/5949116/files/Patient1.zip", ),
    ("Patient2.zip", "https://zenodo.org/record/5949116/files/Patient2.zip", ),
    ("Patient3.zip", "https://zenodo.org/record/5949116/files/Patient3.zip", ),
    ("Patient4.zip", "https://zenodo.org/record/5949116/files/Patient4.zip", ),
]:
    example_file = raw_dir / example_file_name
    if not example_file.exists():
        request.urlretrieve(example_file_url, example_file)
        
panel_file = base_dir / "panel.csv"
if not panel_file.exists():
    request.urlretrieve("https://zenodo.org/record/6642699/files/panel.csv",
                        panel_file)

# %% [markdown]
# ## Extract images from `.mcd` files
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/preprocessing/#external-images

# %% [markdown]
# ### Unzip raw data files
#
# zip folders should contain one `.mcd` file and all the associated `.txt` files.

# %%
# Extract .mcd files
helpers.extract_zips(path=raw_dir, suffix=".mcd", dest=raw_dir)

# %%
# Extract .txt files
helpers.extract_zips(path=raw_dir, suffix=".txt", dest=raw_dir)

# %% [markdown]
# ### Import the panel
# The antibody panel file should be placed in the `examples` folder and meet the steinbock format: https://bodenmillergroup.github.io/steinbock/latest/file-types/#panel.  
#
# Customized panels should contain the following columns:
# + `channel`: unique channel id, typically metal and isotope mass (e.g. `Ir191`)
# + `name`: unique channel name.
# + `deepcell`: channels to use for segmentation (1=nuclear, 2=membrane, empty/NaN=ignored).
# + `keep`: *(optional)* 1 for channels to preprocess, 0 for channels to ignore

# %%
panel = pd.read_csv(base_dir / "panel.csv")
panel.head()

# %% [markdown]
# ### Create panel from mcd files
# Alternatively, the panel can directly be created from `.mcd` files.
#
# In this case, the panel should be modified as following:
# - Define which channels to retain for downstream processing (modify the `keep` column).
# - Define channels to use for deep cell segmentation (see below).
# - Additional modifications can be made (e.g., rename channel names) if needed.

# %%
create_panel_from_mcd = True

# %%
if create_panel_from_mcd:
    # Create the panel
    panel = imc.create_panel_from_mcd_files(imc.list_mcd_files(raw_dir))

    # Channels that will not be keeped
    channels_to_discard = ["ArAr80", "Xe131", "Xe134", "Ba136", "La138", "Pt196", "Pb206"]
    panel.loc[panel["channel"].isin(channels_to_discard), "keep"] = False

    # Channels for cell segmentation
    nuclear_channels = ["In113", "Ir191", "Ir193"]
    membrane_channels = ["Sm147", "Sm149", "Sm152", "Ho165", "Yb173"]
    panel.loc[panel["channel"].isin(nuclear_channels), "deepcell"] = 1
    panel.loc[panel["channel"].isin(membrane_channels), "deepcell"] = 2

# %% [markdown]
# Subset the panel to retain only channels indicated in the `keep` column

# %%
panel = panel[panel["keep"] == 1]
panel.head()

# %% [markdown]
# ### Convert to tiff
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/preprocessing/#image-conversion
#
# #### Settings
# Image stacks are extracted from the acquisitions in `.tiff` format.

# %%
extract_metadata = True

# Value for hot pixel filtering (see the documentation)
hpf = 50

# %% [markdown]
# #### Image conversion
# Extract image stacks from IMC acquisitions (stored in the `img` subfolder) and export metadata as `images.csv`.

# %%
image_info_data = pd.DataFrame()

for mcd_file, acquisition, img, matched_txt, recovered in imc.try_preprocess_images_from_disk(
    mcd_files = imc.list_mcd_files(raw_dir),
    txt_files = imc.list_txt_files(raw_dir),
    hpf = hpf,
    channel_names = panel["channel"]
):
    img_file = Path(img_dir) / f"{mcd_file.stem}_{acquisition.description}.tiff"
    io.write_image(img, img_file)

    if extract_metadata :
        image_info = helpers.extract_metadata(img_file, mcd_file, img, acquisition, matched_txt, recovered)
        image_info_data = pd.concat([image_info_data, image_info])
        
if extract_metadata:
    image_info_data.to_csv(base_dir / "images.csv", index=False)

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
channelwise_zscore = True
channelwise_minmax = False
aggr_func = np.sum

# Define channels to use for segmentation (from the panel file)
channel_groups = imc_panel["deepcell"].values
channel_groups = np.where(channel_groups == 0, np.nan, channel_groups) # make sure unselected chanels are set to nan

# %% [markdown]
# #### Generate segmentation stacks

# %%
for img_path in sorted(Path(img_dir).glob("*.tiff")):
    img = io.read_image(img_path)
    if channelwise_minmax:
        img = helpers.norm_minmax(img)
    
    if channelwise_zscore:
        img = helpers.norm_zscore(img)
    
    if channel_groups is not None:
        img = helpers.segstack_channels(img, channel_groups, aggr_func)
    
    img_file = Path(segstack_dir) / f"{img_path.name}"
    io.write_image(img, img_file)

# %% [markdown]
# #### Check segmentation stacks

# %%
# List segmentation stacks
segstacks = sorted(Path(segstack_dir).glob("*.tiff"))

# Select a random image
rng = np.random.default_rng()
ix = rng.choice(len(segstacks))

# Display nuclear and membrane/cytoplasm images
fig, ax = plt.subplots(1, 2, figsize=(30, 30))

img = io.read_image(segstacks[ix])
ax[0].imshow(img[0,:,:], vmin=0, vmax=10) # adjust vmax if needed (lower value = higher intensity)
ax[0].set_title(segstacks[ix].stem + ": nuclei")

img = io.read_image(segstacks[ix])
ax[1].imshow(img[1,:,:], vmin=0, vmax=10) # adjust vmax if needed (lower value = higher intensity)
ax[1].set_title(segstacks[ix].stem + ": membrane")

# %% [markdown]
# ### Segment cells
#
# `segmentation_type` should be one of [`whole-cell`, `nuclear`, `both`].  
# If `both` is selected, nuclear and whole-cell masks will be generated in separate subfolders.  
#
# Several post-processing arguments can be passed to the deepcell application, the defaults are selected below. Cell labels can also be expanded by defining an `expansion_distance` (mostly useful for nuclear segmentation).

# %%
# Segmentation type
segmentation_type = "both"

# Post-processing arguments for whole-cell segmentation
kwargs_whole_cell =  {
    'maxima_threshold': 0.075,
    'maxima_smooth': 0,
    'interior_threshold': 0.2,
    'interior_smooth': 2,
    'small_objects_threshold': 15,
    'fill_holes_threshold': 15,
    'radius': 2
}

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

# Mask pixel expansion (0 = no expansion)
expansion_distance = 0

# %%
app = Mesmer()

for stack in segstacks:
    img = io.read_image(stack)
    img = np.moveaxis(img, 0, 2)
    img = np.expand_dims(img.data, 0)
    
    mask = app.predict(
        img, image_mpp=1, compartment=segmentation_type,
        postprocess_kwargs_whole_cell=kwargs_whole_cell,
        postprocess_kwargs_nuclear=kwargs_nuclear
    )
    
    helpers.save_masks(
        mask, masks_dir, stack.name,
        segmentation_type, expansion_distance
    )

# %%
# # Generating masks using steinbock's function
# for img_path, mask in deepcell.try_segment_objects(
#     img_files = segstacks,
#     application = deepcell.Application.MESMER,
#     pixel_size_um = 1.0,
#     segmentation_type = segmentation_type
# ):
#     mask = expand_labels(mask, distance=float(expansion_distance))
    
#     mask_file = Path(masks_subdir) / f"{img_path.stem}.tiff"
#     io.write_mask(mask, mask_file)

# %% [markdown]
# #### Check segmentation
#
# Adjust the image intensity by modifiying the `max_intensity` variable.  
# For higher magnification images, adjust the coordinates and dimension if needed.

# %%
# Choose either 'nuclear' or 'whole-cell' for downstream processing
segmentation_type = "nuclear"

# %%
# List masks
masks_subdir = masks_dir / segmentation_type
masks = sorted(Path(masks_subdir).glob("*.tiff"))

# Define instensity value for images
max_intensity = 20 # vmax: lower values = higher intensity

# Select a random image
ix = rng.choice(len(masks))
fig, ax = plt.subplots(2, 2, figsize=(30, 30))

# Display image and mask
img = io.read_image(segstacks[ix])
ax[0,0].imshow(img[0,:,:], vmax=max_intensity)
ax[0,0].set_title(segstacks[ix].stem + ": nuclei")

mask = io.read_image(masks[ix])
cmap = ListedColormap(np.random.rand(10**3,3))
cmap.colors[0]=[1,1,1]
ax[0,1].imshow(mask[0,:,:], cmap=cmap)
ax[0,1].set_title(masks[ix].stem +": mask")

## Higher magnification (change coordinates and dimensions if needed)
xstart = 100
ystart = 100
dim = 100

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
for img_path, mask_path, intens in intensities.try_measure_intensities_from_disk(
    img_files = io.list_image_files(img_dir),
    mask_files = io.list_image_files(masks_subdir),
    channel_names = imc_panel["name"],
    intensity_aggregation = intensities.IntensityAggregation.MEAN
):
    intensities_file = Path(intensities_dir) / f"{img_path.name.replace('.tiff', '.csv')}"
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
        "major_axis_length",
        "minor_axis_length",
        "eccentricity",
    ]

# %% [markdown]
# #### Measure region props

# %%
for img_path, mask_path, region_props in regionprops.try_measure_regionprops_from_disk(
    img_files = io.list_image_files(img_dir),
    mask_files = io.list_image_files(masks_subdir),
    skimage_regionprops = skimage_regionprops
):
    
    regionprops_file = Path(regionprops_dir) / f"{img_path.name.replace('.tiff', '.csv')}"
    pd.DataFrame.to_csv(region_props, regionprops_file)

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
dmax = 15
kmax = 5

# %% [markdown]
# #### Measure cell neighbors

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
