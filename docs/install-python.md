# Python package

The *steinbock* toolkit can be used programmatically using the *steinbock* Python package.

In this section, the installation of the *steinbock* Python package is described.

!!! danger "For scripting use only"
    Installing/using the *steinbock* Python package directly is not recommended for regular users. Please use the *steinbock* Docker containers instead.

## Requirements

[Python](https://www.python.org) 3.8 or newer

Tested versions of Python package dependencies can be found in [requirements.txt](https://github.com/BodenmillerGroup/steinbock/blob/main/requirements.txt).

## Installation

The *steinbock* Python package can be installed [from PyPI](https://pypi.org/project/steinbock) as follows:

    pip install steinbock

The following extras are available:

  - `imc` to enable IMC preprocessing functionality
  - `deepcell` to enable DeepCell segmentation functionality
  - `cellpose` to enable Cellpose segmentation functionality
  - `napari` to enable image visualization functionality

## Usage

Please refer to [Python usage](python/intro.md) for usage instructions.
