# Docker container

The *steinbock* toolkit can be used interactively using the *steinbock* Docker container.

In this section, the installation and configuration of the *steinbock* Docker container is described.

## Prerequisites

### Windows

[Install Docker Desktop](https://docs.docker.com/desktop/install/windows-install/)

Make sure to NOT skip step 5 of the interactive installation instructions (adding your user to the docker-users group, if necessary).

Docker Desktop can run in either Hyper-V mode or in WSL 2 mode. To check/choose in which mode Docker Desktop is running, refer to the preferences menu as described [here](https://docs.docker.com/desktop/settings/windows/#general) (Docker Preferences --> General --> Use the WSL 2 based engine). In general, it is recommended to run Docker Desktop in WSL 2 mode for performance reasons, see [here](https://docs.microsoft.com/en-us/windows/wsl/compare-versions).

!!! note "Systems with limited memory resources"
    On systems with limited memory resources, due to a [problem with WSL 2](https://github.com/microsoft/WSL/issues/4166), it may still be advisable to use the Hyper-V mode. This may also be the case if you experience performance losses due to slow disk access (see [here](https://docs.microsoft.com/en-us/windows/wsl/compare-versions))

Make sure to allocate enough system resources to Docker, as the default memory limit of 2GB will likely not be sufficient to run *steinbock* on real-world datasets:

- If and only if Docker Desktop is running in **Hyper-V mode**, configure the memory that Docker Desktop is allowed to use as described [here](https://docs.docker.com/desktop/settings/windows/#advanced) (Docker Preferences --> Resources --> Advanced --> Memory).

- If and only if Docker Desktop is running in **WSL 2 mode**, follow the instructions for [changing global configuration options](https://docs.microsoft.com/en-us/windows/wsl/wsl-config#global-configuration-options-with-wslconfig) to configure the memory that Docker Desktop is allowed to use.

For any subsequent instruction, use the Windows Command Prompt (not the Windows PowerShell).

### Mac OS

!!! note "steinbock on ARM-based Macs"
    The steinbock Docker container currently does not fully work on ARM-based Macs (e.g. M1, M2).

[Install Docker Desktop](https://docs.docker.com/desktop/install/mac-install/)

Make sure to allocate enough system resources to Docker, as the default memory limit of 2GB will likely not be sufficient to run *steinbock* on real-world datasets. In order to do so, configure the memory that Docker Desktop is allowed to use as described [here](https://docs.docker.com/desktop/settings/mac/#advanced) (Docker Preferences --> Resources --> Advanced --> Memory).

For any subsequent instruction, use the Mac OS Terminal.

### Linux

[Install Docker Server/Engine](https://docs.docker.com/engine/install/#server)

Follow the [post-installation steps for Linux](https://docs.docker.com/engine/install/linux-postinstall/)

To run the *steinbock* Docker container with NVIDIA GPU support (optional), install the proper drivers and verify that your GPU is running and accessible. Install the `nvidia-container-runtime` as described [here](https://docs.docker.com/config/containers/resource_constraints/#access-an-nvidia-gpu) and restart your system.

For any subsequent instruction, use the Linux Terminal.

## Installation

In principle, the *steinbock* Docker container can be run on any Docker-enabled platform:

    docker run ghcr.io/bodenmillergroup/steinbock

For reproducibility, it is recommended to always pull a specific release, e.g.:

    docker run ghcr.io/bodenmillergroup/steinbock:0.16.1

To run the *steinbock* Docker container with NVIDIA GPU support (Linux only):

    docker run --gpus all ghcr.io/bodenmillergroup/steinbock:0.16.1-gpu

[Bind mounts](https://docs.docker.com/storage/bind-mounts/) can be used to make data from the host system available to the Docker container (see below). Commands that launch a graphical user interface may require further system configuration and additional arguments to `docker run` as outlined in the following.

### Windows

On the command line, use the following command to run the *steinbock* Docker container:

    docker run -v "C:\Data":/data -p 8888:8888 -e DISPLAY=host.docker.internal:0 ghcr.io/bodenmillergroup/steinbock:0.16.1

In the command above, adapt the bind mount path to your data/working directory (`C:\Data`; no trailing backslash) and the *steinbock* Docker container version (`0.16.1`) as needed. Specifying the `DISPLAY` environment variable is required only when running graphical user interfaces using X forwarding.

To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` macro:

    doskey steinbock=docker run -p 8888:8888 -v "C:\Data":/data ghcr.io/bodenmillergroup/steinbock:0.16.1 $*

The created macro is retained for the current session and enables running `steinbock` from the current command line without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Windows"
    To allow the *steinbock* Docker container to run graphical user interfaces (e.g. Ilastik, CellProfiler, napari) using X forwarding, [VcXsrv](https://sourceforge.net/projects/vcxsrv/) is required. Running *steinbock* with VcXsrv is untested and therefore undocumented; please do not hesitate to [file a GitHub issue](https://github.com/BodenmillerGroup/steinbock/issues) if you would like to contribute to this documentation.

### Mac OS

On the terminal, use the following command to run the *steinbock* Docker container (Docker must be running):

    docker run -v /path/to/data:/data --platform linux/amd64 -u $(id -u):$(id -g) -p 8888:8888 -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY=host.docker.internal:0 ghcr.io/bodenmillergroup/steinbock:0.16.1

In the command above, adapt the bind mount path to your data/working directory (`/path/to/data`) and the *steinbock* Docker container version (`0.16.1`) as needed. Specifying the `/tmp/.X11-unix` bind mount, the `~/.Xauthority` bind mount and the `DISPLAY` environment variable are required only when running graphical user interfaces using X forwarding.

To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    alias steinbock="docker run -v /path/to/data:/data --platform linux/amd64 -u $(id -u):$(id -g) -p 8888:8888 -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/home/steinbock/.Xauthority:ro -e DISPLAY=host.docker.internal:0 ghcr.io/bodenmillergroup/steinbock:0.16.1"

The created command alias is retained for the current session and enables running `steinbock` from the current terminal without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Mac OS"
    To allow the *steinbock* Docker container to run graphical user interfaces (e.g. Ilastik, CellProfiler, napari) using X forwarding, first install and launch [XQuartz](https://www.xquartz.org/). Then, open *XQuartz* > *Security* > *Preferences* and tick *Allow connections from network clients*. Log out of your user account and login again; restart Docker and XQuartz. Finally, to allow the local root user (i.e., the user running the Docker daemon) to access the running XQuartz X server:

        xhost +localhost

### Linux

On the terminal, use the following command to run the *steinbock* Docker container:

    docker run -v /path/to/data:/data -u $(id -u):$(id -g) --network host -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY ghcr.io/bodenmillergroup/steinbock:0.16.1

To run the *steinbock* Docker container with NVIDIA GPU support, use `-gpu` Docker image instead:

    docker run -v /path/to/data:/data -u $(id -u):$(id -g) --network host -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY --gpus all ghcr.io/bodenmillergroup/steinbock:0.16.1-gpu

In the commands above, adapt the bind mount path to your data/working directory (`/path/to/data`) and the *steinbock* Docker container version (`0.16.1`) as needed. Specifying the `host` network mode, the `/tmp/.X11-unix` bind mount and the `DISPLAY` environment variable are required only when running graphical user interfaces using X forwarding.

To simplify the use of the *steinbock* command-line interface, it is recommended to set up a `steinbock` command alias:

    alias steinbock="docker run -v /path/to/data:/data -u $(id -u):$(id -g) --network host -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY ghcr.io/bodenmillergroup/steinbock:0.16.1"

To run the *steinbock* Docker container with NVIDIA GPU support, use `-gpu` Docker image instead:

    alias steinbock="docker run -v /path/to/data:/data -u $(id -u):$(id -g) --network host -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY --gpus all ghcr.io/bodenmillergroup/steinbock:0.16.1-gpu"

The created command alias is retained for the current session and enables running `steinbock` from the current terminal without typing the full Docker command, for example:

    steinbock --version

!!! note "Graphical user interfaces on Linux"
    To allow the *steinbock* Docker container to run graphical user interfaces (e.g. Ilastik, CellProfiler, napari) using X forwarding, if necessary, allow the local root user to access the running X server:

        xhost +local:root

## Usage

Please refer to [command-line usage](cli/intro.md) for usage instructions.

!!! note "Getting help"
    The *steinbock* Docker container is under active development. If you are experiencing issues, you are more than welcome to [file an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues). However, please understand that only issues directly concerning *steinbock* can be addressed. For user support with Docker, command line usage, etc., please refer to your local IT administrator.
