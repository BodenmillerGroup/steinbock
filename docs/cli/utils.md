# Utilities

Various built-in utilities are exposed via *steinbock*'s `utils` command.

## Matching

The following command will, for each pair of masks, identify overlapping (intersecting) objects:

    steinbock utils match cell_masks tumor_masks -o matched_objects

Here, `cell_masks` and `tumor_masks` are path to directories containing masks. Masks from both directories are matched by name. This will generate tables in CSV format (undocumented, one file per mask pair), with each row indicating IDs from overlapping objects in both masks.

!!! note "Usage example"
    Identifying overlapping objects can be useful in multi-segmentation contexts. For example, one may be interested in cells from tumor regions only, in which case two segmentation workflows would be followed sequentially:
    
      - "Global" tumor/stroma segmentation
      - "Local" cell segmentation

    Afterwards, one could match the generated masks to restrict downstream analyses to cells in tumor regions.

## Mosaics

This *steinbock* utility for tiling and stitching images allows the processing of large image files.

!!! note "Data type"
    Unlike other *steinbock* operations, all `mosaic` commands load and save images in their original data type.

### Tiling images

The following command will split all images in `img_full` into tiles of 4096x4096 pixels (the recommended maximum image size for *steinbock* on local installations) and save them to `img`:

    steinbock utils mosaics tile img_full -s 4096 -o img

The created image tiles will have the following file name, where `{IMG}` is the original file name (without extension), `{X}` and `{Y}` indicate the tile position (in pixels) and `{W}` and `{H}` indicate the tile width and height, respectively:

    {IMG}_tx{X}_ty{Y}_tw{W}_th{H}.tiff

### Stitching mosaics

The following command will stitch all mask tiles in `masks` (following the file conventions above) to assemble masks of original size and save them to `masks_full`:

    steinbock utils mosaics stitch masks -o masks_full
