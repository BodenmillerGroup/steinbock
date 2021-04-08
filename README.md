# steinbock

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/BodenmillerGroup/steinbock/docs?label=docs)
![GitHub License](https://img.shields.io/github/license/BodenmillerGroup/steinbock)
![GitHub Issues](https://img.shields.io/github/issues/BodenmillerGroup/steinbock)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/BodenmillerGroup/steinbock?label=pull%20requests)
![Docker Build Status](https://img.shields.io/docker/build/jwindhager/steinbock)
![Docker Image Version (latest semver)](https://img.shields.io/docker/v/jwindhager/steinbock?label=docker%20version&sort=semver)

Dockerized multi-channel image segmentation framework

Documentation is available at https://bodenmillergroup.github.io/steinbock


## Requirements

Docker


## Installation

To pull the most recent version of steinbock:

    docker pull jwindhager/steinbock:latest


## Usage

To run the steinbock Docker container:

    docker run -v /mnt/data:/data steinbock --help

Replace `/mnt/data` with the path to your data directory.

To run the steinbock Docker container with X11 enabled (Linux/MacOS):

    xhost +local:root  # this is unsafe!
    docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/root/.Xauthority:ro steinbock --help

On Windows platforms, it is recommended to run GUI applications (e.g. Ilastik, Cellprofiler) natively.

For repeated use, it is recommended to create a shell alias (Linux/MacOS):

    alias steinbock="docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/root/.Xauthority:ro steinbock"

Further documentation is available at https://bodenmillergroup.github.io/steinbock


## Authors

- Jonas Windhager [jonas.windhager@uzh.ch](mailto:jonas.windhager@uzh.ch)


## Contributing

[Contributing](CONTRIBUTING.md)


## Changelog

[Changelog](CHANGELOG.md)


## License

[MIT](LICENSE.md)
