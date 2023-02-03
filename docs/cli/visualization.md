# Visualization

## Images

In this step, images and masks are visualized using the [napari](https://napari.org) image viewer.

!!! danger "Experimental feature"
    This is a highly experimental feature. It requires OpenGL-enabled X forwarding and will not work on most systems. Alternatively, one can resort to Xpra-enabled Docker containers to run a steinbock-enabled desktop environment within a web browser (undocumented).

!!! note "Docker and graphical user interfaces"
    Running napari using steinbock Docker containers requires support for graphical user interfaces (e.g. X forwarding).

To open the image `myimage.tiff` (and, optionally, the corresponding mask) in napari:

    steinbock view myimage.tiff
