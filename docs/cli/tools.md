# Tools

Various applications and tools are exposed via *steinbock*'s `tools` command.

## Ilastik

To run the Ilastik application:

    steinbock tools ilastik

Without additional arguments, this will start the graphical user interface of Ilastik.

!!! note "Graphical user interfaces"
    If *steinbock* exits with a warning message, ensure that *steinbock* is [configured](/install/#configuration) for running graphical user interfaces.

## CellProfiler

To run the CellProfiler application:

    steinbock tools cellprofiler

Without additional arguments, this will start the graphical user interface of CellProfiler.

!!! note "Graphical user interfaces"
    If *steinbock* exits with a warning message, ensure that *steinbock* is [configured](/install/#configuration) for running graphical user interfaces.

## Mosaics

This *steinbock* tool for tiling and stitching images allows the processing of large images.

!!! note "Data type"
    Unlike other *steinbock* operations, all `mosaic` commands load and save images in their original data type.

### Tiling

The following command will split all images in `img_full` into tiles of 4096x4096 pixels (the recommended maximum image size for *steinbock* on local installations) and save them to `img`:

    steinbock tools mosaic tile -o img -s 4096 img_full

The created image tiles will have the following file name, where `{IMG}` is the original file name (without extension), `{X}` and `{Y}` indicate the tile position (in pixels) and `{W}` and `{H}` indicate the tile width and height, respectively:

    {IMG}_tx{X}_ty{Y}_tw{W}_th{H}.tiff

### Stitching

The following command will stitch all mask tiles in `masks` (following the file conventions above) to assemble masks of original size and save them to `masks_full`:

    steinbock tools mosaic stitch -o masks_full masks
