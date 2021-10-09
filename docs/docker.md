# Docker

The *steinbock* framework can be used interactively using the *steinbock* Docker container.

In this section, the installation and configuration of the *steinbock* Docker container is described.

!!! note "Prerequisites"
    To make efficient use of the *steinbock* Docker container, basic command line skills are absolutely required. Furthermore, understanding key concepts of containerization using Docker may be helpful in resolving issues.

## Requirements

[Install Docker](https://docs.docker.com/get-docker/)

!!! note "System resources"
    On Windows and MacOS hosts, make sure to allocate enough system resources to Docker. In particular, Docker's default memory limit of 2GB will likely not be sufficient to run steinbock on real-world datasets. To increase the memory limit, please refer to the Docker manual for [Windows](https://docs.docker.com/desktop/windows/) and [MacOS](https://docs.docker.com/desktop/mac/).

Make Docker available to non-root users: Linux users can follow the [post-installation steps for Linux](https://docs.docker.com/engine/install/linux-postinstall/), Windows users need to add the current user to the `docker-users` group. For MacOS, no further setup is required.

!!! note "Adding a user to the `docker-users` group on Windows hosts"
    On Windows hosts, to add a user to the `docker-users` group using the command line (as administrator):

        net localgroup /add docker-users <username>
		
	Replace `<username>` with the name of the user (for domain accounts, use the `<domain>\<username>` format).

## Installation

In principle, the *steinbock* Docker container can be run on any Docker-enabled platform:

    docker run ghcr.io/bodenmillergroup/steinbock

For reproducibility, it is recommended to always pull a specific release, e.g.:

    docker run ghcr.io/bodenmillergroup/steinbock:0.8.1

[Bind mounts](https://docs.docker.com/storage/bind-mounts/) can be used to make data from the host system available to the Docker container (see below). Commands that launch a graphical user interface may require further system configuration and additional arguments to `docker run` as outlined in the following.


### Windows

On the command line, use the following command to run the *steinbock* Docker container:

    docker run -v "C:\Data":/data ghcr.io/bodenmillergroup/steinbock:0.8.1

In the command above, adapt the bind mount path to your data/working directory (`C:\Data`) and the *steinbock* Docker container version (`0.8.1`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    doskey steinbock=docker run -v "C:\Data":/data ghcr.io/bodenmillergroup/steinbock:0.8.1 $*

The created command alias is retained for the current session and enables running `steinbock` from the current command line without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Windows hosts"
    Commands that launch a graphical user interface (e.g. for Ilastik, CellProfiler) will not work on Windows hosts. It is recommended to run these programs directly on the Windows host, if graphical user interfaces are required. For compatibility, versions of third-party applications can be found in the [*steinbock* Dockerfile](https://github.com/BodenmillerGroup/steinbock/blob/main/Dockerfile).

### Linux

On the terminal, use the following command to run the *steinbock* Docker container:

    docker run -v /path/to/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -u $(id -u):$(id -g) -e DISPLAY ghcr.io/bodenmillergroup/steinbock:0.8.1

In the command above, adapt the bind mount path to your data/working directory (`/path/to/data`) and the *steinbock* Docker container version (`0.8.1`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    alias steinbock="docker run -v /path/to/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -u $(id -u):$(id -g) -e DISPLAY ghcr.io/bodenmillergroup/steinbock:0.8.1"

The created command alias is retained for the current session and enables running `steinbock` from the current terminal without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Linux hosts"
    To allow the *steinbock* Docker container to run graphical user interfaces, if necessary, allow the local root user (i.e., the user running the Docker daemon) to access the running X server:

        xhost +local:root

### MacOS

On the terminal, use the following command to run the *steinbock* Docker container (Docker must be running):

    docker run -v /path/to/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -u $(id -u):$(id -g) -e DISPLAY=$(hostname):0 ghcr.io/bodenmillergroup/steinbock:0.8.1

In the command above, adapt the bind mount path to your data/working directory (`/path/to/data`) and the *steinbock* Docker container version (`0.8.1`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    alias steinbock="docker run -v /path/to/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -u $(id -u):$(id -g) -e DISPLAY=$(hostname):0 ghcr.io/bodenmillergroup/steinbock:0.8.1"

The created command alias is retained for the current session and enables running `steinbock` from the current terminal without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on MacOS hosts"
    To allow the *steinbock* Docker container to run graphical user interfaces, first install and start [XQuartz](https://www.xquartz.org/). Then, open *XQuartz* > *Security* > *Preferences* and tick *Allow connections from network clients*. Log out of your user account and login again; restart Docker and XQuartz. Finally, to allow the local root user (i.e., the user running the Docker daemon) to access the running XQuartz X server:

        xhost + $(hostname)

## Usage

Please refer to [CLI usage](cli/intro.md) for usage instructions.

!!! note "Getting help"
    The *steinbock* Docker container is under active development. If you are experiencing issues, you are more than welcome to [file an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues). However, please understand that only issues directly concerning *steinbock* can be addressed. For user support with Docker, command line usage, etc., please refer to your local IT administrator.