# steinbock

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/BodenmillerGroup/steinbock/docs?label=docs)
![GitHub License](https://img.shields.io/github/license/BodenmillerGroup/steinbock)
![GitHub Issues](https://img.shields.io/github/issues/BodenmillerGroup/steinbock)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/BodenmillerGroup/steinbock?label=pull%20requests)
![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/jwindhager/steinbock)
![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jwindhager/steinbock?label=docker%20version&sort=semver)

Dockerized multi-channel image segmentation framework

The steinbock repository comprises the following components:
- Python package with integrated interactive command-line interface (CLI)
- Docker container exposing steinbock, with third-party software (e.g. Ilastik, CellProfiler) pre-installed

Multi-channel image segmentation approaches currently implemented in steinbock:
- Zanotelli et al. _ImcSegmentationPipeline: A pixel classification-based multiplexed image segmentation pipeline_. Zenodo, 2017.

Documentation is available at https://bodenmillergroup.github.io/steinbock


## Requirements

[Install Docker](https://docs.docker.com/get-docker/)


## Installation

To pull the most recent version of steinbock (not recommended):

    docker pull jwindhager/steinbock

For reproducibility, it is recommended to explicitly specify the [steinbock release](https://github.com/BodenmillerGroup/steinbock/releases):

    docker pull jwindhager/steinbock:0.3.0


## Usage

To run the steinbock Docker container:

    docker run -v /mnt/data:/data jwindhager/steinbock

Replace `/mnt/data` with the path to your data directory.

To run the steinbock Docker container with X11 enabled (Linux/MacOS):

    xhost +local:root
    docker run -v /mnt/data:/data -v /tmp/.X11-unix -v ~/.Xauthority:/root/.Xauthority:ro -e DISPLAY jwindhager/steinbock

On Windows platforms, it is recommended to run GUI applications (e.g. Ilastik, Cellprofiler) natively.

For repeated use, it is recommended to create a shell alias (Linux/MacOS):

    alias steinbock="docker run -v /mnt/data:/data -v /tmp/.X11-unix -v ~/.Xauthority:/root/.Xauthority:ro -e DISPLAY jwindhager/steinbock"

Further documentation is available at https://bodenmillergroup.github.io/steinbock


## Authors

- [Jonas Windhager](mailto:jonas.windhager@uzh.ch)


## Contributing

[Contributing](https://github.com/BodenmillerGroup/steinbock/blob/main/CONTRIBUTING.md)


## Changelog

[Changelog](https://github.com/BodenmillerGroup/steinbock/blob/main/CHANGELOG.md)


## License

[MIT](https://github.com/BodenmillerGroup/steinbock/blob/main/LICENSE.md)
