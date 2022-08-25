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
import tifffile
import xtiff

from pathlib import Path

from steinbock import io
from steinbock.preprocessing import external

import helpers

# %% [markdown]
# # Multiplex images preprocessing pipeline
#
# This pipeline will run image segmentation within the steinbock workframe. It can be applied to any multiplex image stacks. The full pipeline consists of three separate notebooks that have to be run successively: `preprocessing` (current notebook), `segmentation`, and `measurement`.
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
# Edit the working directory if needed (by default, the `examples` folder).
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
working_dir = Path(".")

# Paths to zipped acquisition files
raw_dir = working_dir / "raw"

# Output directories
img_dir = working_dir / "img"

# Create directories (if they do not already exist)
raw_dir.mkdir(exist_ok=True)
img_dir.mkdir(exist_ok=True)

# %% [markdown]
# ## Antibody panel
#
# ### Import the panel
# The antibody panel should meet the steinbock format: https://bodenmillergroup.github.io/steinbock/latest/file-types/#panel  
#
# Customized panels should contain the following columns:
# + `channel`: unique channel id, typically metal and isotope mass (e.g. `Ir191`) or fluorophore.
# + `name`: unique channel name.
# + `deepcell`: channels to use for segmentation (1=nuclear, 2=membrane, empty/NaN=ignored).
# + `keep`: *(optional)* 1 for channels to preprocess, 0 for channels to ignore

# %%
panel_file = working_dir / "panel.csv"

# %%
panel = io.read_panel(panel_file)
nb_of_channels = len(panel)
panel.head()

# %% [markdown]
# ## Re-shape `.tiff` stacks
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

# %%
# !conda list
