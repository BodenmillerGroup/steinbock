# Installation

Here, the installation and configuration of the *steinbock* Docker container is described.

## Requirements

[Install Docker](https://docs.docker.com/get-docker/)

## Installation

Pull the latest version of the *steinbock* Docker container:

    docker pull jwindhager/steinbock

For reproducibility, it is recommended to always pull a specific release, e.g.:

    docker pull jwindhager/steinbock:0.3.2

## Configuration

### Windows

!!! danger "Experimental feature"
    Running *steinbock* on Windows platforms is not recommended.

In the following instructions, instead of calling `steinbock`, type:

    docker run -v "C:\data":/data jwindhager/steinbock:0.3.2

In the command above, adapt the path to your *steinbock* data/working directory (`C:\data`) and the *steinbock* Docker container version (`0.3.2`) as needed.

!!! note "Graphical user interfaces on Windows hosts"
    Commands that launch a graphical user interface (e.g., for Ilastik, CellProfiler) will not work on Windows hosts. It is recommended to run these programs directly on the Windows host, if graphical user interfaces are required.

### Linux/MacOS

Create an alias for running the *steinbock* Docker container:

    alias steinbock="docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/root/.Xauthority:ro -e DISPLAY jwindhager/steinbock:0.3.2"

In the command above, adapt the path to your *steinbock* data/working directory (`/mnt/data`) and the *steinbock* Docker container version (`0.3.2`) as needed. The created alias enables running `steinbock` without typing the full Docker command everytime.

If necessary, allow the Docker container to run graphical user interfaces:

    xhost +local:root

Check whether *steinbock* runs:

    steinbock