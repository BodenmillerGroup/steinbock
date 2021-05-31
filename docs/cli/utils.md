# Utilities

Various utilities are exposed via *steinbock*'s `tools` command.

## Masks

### Mask matching

The following command will, for each mask pair, identify overlapping (i.e., *intersecting*) objects:

    steinbock tools masks match -o object_mappings cell_masks tumor_masks

Here, `cell_masks` and `tumor_masks` are path to directories containing masks. Masks from both directories are matched by name. This will generate tables in CSV format (undocumented, one file per mask pair), with each row indicating IDs from overlapping objects in both masks.

!!! note "Usage example"
    Identifying overlapping objects can be useful in multi-segmentation contexts. For example, one may be interested in cells from tumor regions only, in which case two segmentation workflows would be followed sequentially:
    
      - "Global" tumor/stroma segmentation
      - "Local" cell segmentation

    Afterwards, one could match the generated masks to restrict downstream analyses to cells in tumor regions.

## Mosaics

This *steinbock* tool for tiling and stitching images allows the processing of large images.

!!! note "Data type"
    Unlike other *steinbock* operations, all `mosaic` commands load and save images in their original data type.

### Tiling images

The following command will split all images in `img_full` into tiles of 4096x4096 pixels (the recommended maximum image size for *steinbock* on local installations) and save them to `img`:

    steinbock tools mosaics tile -o img -s 4096 img_full

The created image tiles will have the following file name, where `{IMG}` is the original file name (without extension), `{X}` and `{Y}` indicate the tile position (in pixels) and `{W}` and `{H}` indicate the tile width and height, respectively:

    {IMG}_tx{X}_ty{Y}_tw{W}_th{H}.tiff

### Stitching mosaics

The following command will stitch all mask tiles in `masks` (following the file conventions above) to assemble masks of original size and save them to `masks_full`:

    steinbock tools mosaics stitch -o masks_full masks
