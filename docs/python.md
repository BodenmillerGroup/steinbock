# Python

The *steinbock* framework can be used programmatically using the *steinbock* Python package.

In this section, the installation of the *steinbock* Python package is described.

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

        pip install --upgrade deepcell==0.11.0
        pip install --upgrade -r requirements.txt
        pip install --upgrade "steinbock[all]"

## Usage

Please refer to [Python usage](python/intro.md) for usage instructions.
