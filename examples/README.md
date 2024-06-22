# Examples

This directory contains scripts and notebooks exemplifying the use of steinbock with Python.


## Installation

**Note:** Installation is currently only supported on `ubuntu`.  

To run the current pipeline, a conda environment can be installed as follows:

```
conda create -n steinbock python=3.8
conda activate steinbock
pip install --upgrade -r requirements_deepcell.txt
pip install --no-deps deepcell==0.12.3
pip install --upgrade -r requirements.txt
pip install --no-deps "steinbock[all]"
conda install -c conda-forge jupyter jupyterlab
```
The [requirements.txt](https://github.com/BodenmillerGroup/steinbock/blob/main/requirements.txt)
and [requirements_deepcell.txt](https://github.com/BodenmillerGroup/steinbock/blob/main/requirements_deepcell.txt)
files are located in the root folder of the `steinbock` repository.  

Up-to-date compatible package versions can be found here:
https://bodenmillergroup.github.io/steinbock/latest/install-python/
("Package version conflicts").

## Running the pipeline

For IMC data processing, the following notebooks should be run:
- `01_preprocessing_imc.ipynb`
- `02_segmentation_deepcell.ipynb`
- `03_measurement.ipynb`
