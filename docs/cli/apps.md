# Apps

The *steinbock* Docker container exposes various third-party apps via the `apps` command.

!!! note "Graphical user interfaces"
    Graphical user interfaces are not supported on Windows hosts, see [Docker configuration](../install-docker.md#windows).

## Ilastik

To run [Ilastik](https://www.ilastik.org):

    steinbock apps ilastik

Without additional arguments, this will start the graphical user interface of Ilastik.

## CellProfiler

To run [CellProfiler](https://cellprofiler.org):

    steinbock apps cellprofiler

Without additional arguments, this will start the graphical user interface of CellProfiler.
