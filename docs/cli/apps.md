# Apps

The *steinbock* Docker container exposes various third-party apps via the `apps` command.

## Ilastik

!!! note "Docker and graphical user interfaces"
    Running Ilastik using steinbock Docker containers requires support for graphical user interfaces (e.g. X forwarding).

To run [Ilastik](https://www.ilastik.org):

    steinbock apps ilastik

Without additional arguments, this will start the graphical user interface of Ilastik.

## CellProfiler

!!! note "Docker and graphical user interfaces"
    Running CellProfiler using steinbock Docker containers requires support for a graphical user interfaces (e.g. X forwarding).

To run [CellProfiler](https://cellprofiler.org):

    steinbock apps cellprofiler

Without additional arguments, this will start the graphical user interface of CellProfiler.

## Jupyter Notebook

!!! note "Port"
    Jupyter Notebook requires the specified port exposed and published via Docker.

To run [Jupyter Notebook](https://jupyter.org):

    steinbock apps jupyter

Without additional arguments, this will start Jupyter Notebook on http://localhost:8888.

## Jupyter Lab

!!! note "Port"
    Jupyter Lab requires the specified port exposed and published via Docker.

To run [Jupyter Lab](https://jupyter.org):

    steinbock apps jupyterlab

Without additional arguments, this will start Jupyter Lab on http://localhost:8888.
