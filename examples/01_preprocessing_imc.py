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
from urllib import request

from steinbock import io
from steinbock.preprocessing import imc

import helpers

# %% [markdown]
# # IMC preprocessing pipeline
#
# The full pipeline consists of three separate notebooks that have to be run successively: `preprocessing` (current notebook), `segmentation`, and `measurement`.
#
# Here, we will extract image data from IMC aquisitions located in the `raw` folder and generate `.tiff` image stacks.
#
# Before running your own script please check the [steinbock documentation](https://bodenmillergroup.github.io/steinbock).
#
# *Installation*  
# To install the required python environment, follow the instructions here: https://bodenmillergroup.github.io/steinbock/latest/install-python/

# %% [markdown]
# ## Settings
#
# ### Input and output directories
# Edit the working directory if needed (by default, the `examples` folder).
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

# Paths to zipped acquisition files
raw_dir = working_dir / "raw"

# Output directories
img_dir = working_dir / "img"

# Create directories (if they do not already exist)
raw_dir.mkdir(exist_ok=True)
img_dir.mkdir(exist_ok=True)

# %% [markdown]
# ## Download IMC example data
# This section downloads IMC example raw data and the associated antibody panel file used for the experiment. The IMC raw data will be stored in the `raw` folder and the panel will be stored in the working directory.  
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
        
panel_file = working_dir / "panel.csv"
if not panel_file.exists():
    request.urlretrieve("https://zenodo.org/record/6642699/files/panel.csv",
                        panel_file)

# %% [markdown]
# ## Unzip raw data files
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/preprocessing/#external-images
#
# zip folders should contain one `.mcd` file and all the associated `.txt` files.

# %%
# Extract .mcd files
helpers.extract_zips(path=raw_dir, suffix=".mcd", dest=raw_dir)

# %%
# Extract .txt files
helpers.extract_zips(path=raw_dir, suffix=".txt", dest=raw_dir)

# %% [markdown]
# ## Antibody panel
#
# ### Import the panel
# The antibody panel file should be placed in the working directory (`examples` folder by default) and meet the steinbock format: https://bodenmillergroup.github.io/steinbock/latest/file-types/#panel.  
#
# Customized panels should contain the following columns:
# + `channel`: unique channel id, typically metal and isotope mass (e.g. `Ir191`)
# + `name`: unique channel name.
# + `deepcell`: channels to use for segmentation (1=nuclear, 2=membrane, empty/NaN=ignored).
# + `keep`: *(optional)* 1 for channels to preprocess, 0 for channels to ignore

# %%
panel_file = working_dir / "panel.csv"

# %%
panel = io.read_panel(panel_file)
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
create_panel_from_mcd = False

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
    
    # Subset channels
    panel = panel[panel["keep"] == 1]
    print(panel.head())

# %% [markdown]
# ### Write out the panel

# %%
io.write_panel(panel, panel_file)

# %% [markdown]
# ## Convert to images to tiff
#
# Documentation: https://bodenmillergroup.github.io/steinbock/latest/cli/preprocessing/#image-conversion
#
# ### Settings
# Image stacks are extracted from the acquisitions in `.tiff` format.

# %%
extract_metadata = True

# Value for hot pixel filtering (see the documentation)
hpf = 50

# %% [markdown]
# ### Image conversion
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
    image_info_data.to_csv(working_dir / "images.csv", index=False)

# %%
# !conda list
