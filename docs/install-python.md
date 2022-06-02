# Python

The *steinbock* framework can be used programmatically using the *steinbock* Python package.

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

To install all extras, use the `all` extra:

    pip install "steinbock[all]"

!!! note "Package version conflics"
    Some of the dependencies of steinbock are incompatible due to different version requirements. As a workaround, use the following strategy for installing tested combinations of package versions:

        # choose between one of the following:
        # pip install --upgrade -r requirements_deepcell.txt
        # pip install --upgrade -r requirements_deepcell-gpu.txt
        pip install --no-deps deepcell==0.12.0
        pip install --upgrade -r requirements.txt
        pip install "steinbock[all]"

## Usage

Please refer to [Python usage](python/intro.md) for usage instructions.
