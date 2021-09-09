# Docker

The *steinbock* framework can be used interactively using the *steinbock* Docker container.

In this section, the installation and configuration of the *steinbock* Docker container is described.

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

    docker run ghcr.io/bodenmillergroup/steinbock:0.7.3

[Bind mounts](https://docs.docker.com/storage/bind-mounts/) can be used to make data from the host system available to the Docker container (see below). Commands that launch a graphical user interface may require further system configuration and additional arguments to `docker run` as outlined in the following.

### Windows

On the command line, use the following command to run the *steinbock* Docker container:

    docker run -v "C:\Data":/data ghcr.io/bodenmillergroup/steinbock:0.7.3

In the command above, adapt the bind mount path to your data/working directory (`C:\Data`) and the *steinbock* Docker container version (`0.7.3`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    doskey steinbock=docker run -v "C:\Data":/data ghcr.io/bodenmillergroup/steinbock:0.7.3 $*

The created command alias is retained for the current session and enables running `steinbock` from the current command line without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Windows hosts"
    Commands that launch a graphical user interface (e.g. for Ilastik, CellProfiler) will not work on Windows hosts. It is recommended to run these programs directly on the Windows host, if graphical user interfaces are required. For compatibility, versions of third-party applications can be found in the [*steinbock* Dockerfile](https://github.com/BodenmillerGroup/steinbock/blob/main/Dockerfile).

### Linux

On the terminal, use the following command to run the *steinbock* Docker container:

    docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY ghcr.io/bodenmillergroup/steinbock:0.7.3

In the command above, adapt the bind mount path to your data/working directory (`/mnt/data`) and the *steinbock* Docker container version (`0.7.3`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    alias steinbock="docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY ghcr.io/bodenmillergroup/steinbock:0.7.3"

The created command alias is retained for the current session and enables running `steinbock` from the current terminal without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Linux hosts"
    To allow the *steinbock* Docker container to run graphical user interfaces, if necessary, allow the local root user (i.e., the user running the Docker daemon) to access the running X server:

        xhost +local:root

### MacOS

On the terminal, use the following command to run the *steinbock* Docker container:

    docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY=$(hostname):0 ghcr.io/bodenmillergroup/steinbock:0.7.3

In the command above, adapt the bind mount path to your data/working directory (`/mnt/data`) and the *steinbock* Docker container version (`0.7.3`) as needed. To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    alias steinbock="docker run -v /mnt/data:/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY=$(hostname):0 ghcr.io/bodenmillergroup/steinbock:0.7.3"

The created command alias is retained for the current session and enables running `steinbock` from the current terminal without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on MacOS hosts"
    To allow the *steinbock* Docker container to run graphical user interfaces, first install and start [XQuartz](https://www.xquartz.org/). Then, open *XQuartz* > *Preferences* and tick *Allow connections from network clients*. Finally, to allow the local root user (i.e., the user running the Docker daemon) to access the running XQuartz X server:

        xhost + $(hostname)

## Usage

Please refer to [CLI usage](../cli/intro.md) for usage instructions.

!!! note "File permissions"
    By default, the *steinbock* Docker container internally runs as `steinbock` user with user ID (UID) `1000` and group ID (GID) `1000`. Files created from within the container will therefore be owned by the host system user/group matching these IDs. On most Linux systems, by default, this will map to the standard user (e.g. `ubuntu`). 
    
    However, if your user does not match the UID/GID (e.g. on multi-user environments, MacOS), you may not have ownership/write access to files generated by `steinbock`. In this case, you have the following options:

      - **[Beginner]** After creating files with *steinbock*, change their ownership to your account

      - **[Linux only]** Mount `/etc/passwd` and run the Docker container with a user existing on the host: 

            docker run -v /etc/passwd:/etc/passwd:ro -u $(id -u):$(id -g) ...

      - **[Advanced]** Run the *steinbock* Docker container using [singularity](https://sylabs.io/singularity/) (see [here](https://sylabs.io/guides/3.0/user-guide/singularity_and_docker.html)) to minimize abstraction

      - **[Administrator]** Re-build the *steinbock* Docker container from scratch with matching UID/GID ([Dockerfile](https://github.com/BodenmillerGroup/steinbock/blob/main/Dockerfile))

      - **[Developer]** If you would like to provide a workaround for this inconvenience (e.g. automatically change the UID/GID at runtime of the *steinbock* Docker container), you are more than welcome to submit a pull request!

    The data/working directory must be writable by the `steinbock` user from within the *steinbock* Docker container.
