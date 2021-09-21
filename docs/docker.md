# Docker

The *steinbock* framework can be used interactively using the *steinbock* Docker container.

In this section, the installation and configuration of the *steinbock* Docker container is described.

!!! note "Prerequisites"
    To make efficient use of the *steinbock* Docker container, basic command line skills are absolutely required. Furthermore, understanding key concepts of containerization using Docker may be helpful in resolving issues.

## Requirements

[Install Docker](https://docs.docker.com/get-docker/)

Make Docker available to non-root users: Linux/MacOS users can follow the [post-installation steps for Linux](https://docs.docker.com/engine/install/linux-postinstall/), Windows users need to add the current user to the `docker-users` group.

!!! note "Adding a user to the `docker-users` group on Windows hosts"
    On Windows hosts, to add a user to the `docker-users` group using the command line (as administrator):

        net localgroup /add docker-users <username>
		
	Replace `<username>` with the name of the user (for domain accounts, use the `<domain>\<username>` format).

## Installation

In principle, the *steinbock* Docker container can be run on any Docker-enabled platform:

    docker run ghcr.io/bodenmillergroup/steinbock

For reproducibility, it is recommended to always pull a specific release, e.g.:

    docker run ghcr.io/bodenmillergroup/steinbock:0.8.0

[Bind mounts](https://docs.docker.com/storage/bind-mounts/) can be used to make data from the host system available to the Docker container (see below). Commands that launch a graphical user interface may require further system configuration and additional arguments to `docker run` as outlined in the following.

### Windows

On the command line, use the following command to run the *steinbock* Docker container:

    docker run -v "C:\Data":/data ghcr.io/bodenmillergroup/steinbock:0.8.0

In the command above, adapt the bind mount path to your data/working directory (`C:\Data`) and the *steinbock* Docker container version (`0.8.0`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    doskey steinbock=docker run -v "C:\Data":/data ghcr.io/bodenmillergroup/steinbock:0.8.0 $*

The created command alias is retained for the current session and enables running `steinbock` from the current command line without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Windows hosts"
    Commands that launch a graphical user interface (e.g. for Ilastik, CellProfiler) will not work on Windows hosts. It is recommended to run these programs directly on the Windows host, if graphical user interfaces are required. For compatibility, versions of third-party applications can be found in the [*steinbock* Dockerfile](https://github.com/BodenmillerGroup/steinbock/blob/main/Dockerfile).

### Linux

On the terminal, use the following command to run the *steinbock* Docker container:

    docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY ghcr.io/bodenmillergroup/steinbock:0.8.0

In the command above, adapt the bind mount path to your data/working directory (`/mnt/data`) and the *steinbock* Docker container version (`0.8.0`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    alias steinbock="docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY ghcr.io/bodenmillergroup/steinbock:0.8.0"

The created command alias is retained for the current session and enables running `steinbock` from the current terminal without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Linux hosts"
    To allow the *steinbock* Docker container to run graphical user interfaces, if necessary, allow the local root user (i.e., the user running the Docker daemon) to access the running X server:

        xhost +local:root

### MacOS

On the terminal, use the following command to run the *steinbock* Docker container:

    docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY=$(hostname):0 ghcr.io/bodenmillergroup/steinbock:0.8.0

In the command above, adapt the bind mount path to your data/working directory (`/mnt/data`) and the *steinbock* Docker container version (`0.8.0`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    alias steinbock="docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY=$(hostname):0 ghcr.io/bodenmillergroup/steinbock:0.8.0"

The created command alias is retained for the current session and enables running `steinbock` from the current terminal without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on MacOS hosts"
    To allow the *steinbock* Docker container to run graphical user interfaces, first install and start [XQuartz](https://www.xquartz.org/). Then, open *XQuartz* > *Preferences* and tick *Allow connections from network clients*. Finally, to allow the local root user (i.e., the user running the Docker daemon) to access the running XQuartz X server:

        xhost + $(hostname)

## Usage

Please refer to [CLI usage](cli/intro.md) for usage instructions.

## Troubleshooting

!!! note "Getting help"
    The *steinbock* Docker container is under active development. If you are experiencing issues, you are more than welcome to [file an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues). However, please understand that only issues directly concerning *steinbock* can be addressed. For user support with Docker, command line usage, etc., please refer to your local IT administrator.

### File permission issues

The data/working directory must be writable by the host system user and/or group matching the user/group ID (UID/GID) of the user running within the *steinbock* Docker container. By default, the *steinbock* Docker container internally runs as user `steinbock` with UID `1000` and GID `1000`. The data/working directory must therefore be writeable by the host system user and/or group matching these IDs, and files created from within the container will be owned by that user.

Alternatively, you have the following options to run the *steinbock* Docker container:

 - **[Linux only]** Add bind mounts for the `/etc/passwd` and `/etc/groups` files and run the *steinbock* Docker container with the desired (e.g., current) host system user, by supplying the following additional options to the `docker run` command (remember to update your alias):
 
        -v /etc/passwd:/etc/passwd:ro -v /etc/groups:/etc/groups:ro -u $(id -u):$(id -g)

 - **[Singularity]** Run the *steinbock* Docker container using [Singularity](https://sylabs.io/singularity/) (see [here](https://sylabs.io/guides/3.0/user-guide/singularity_and_docker.html))

 - **[Custom build]** Re-build the *steinbock* Docker container from scratch with the UID and GID matching the desired (e.g., current) host system user ([Dockerfile](https://github.com/BodenmillerGroup/steinbock/blob/main/Dockerfile))

If you are a developer and would like to implement a workaround for this inconvenience (e.g. automatically change the UID/GID at runtime of the *steinbock* Docker container), you are more than welcome to submit a pull request!
