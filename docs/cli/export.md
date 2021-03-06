# Data export

Data generated by *steinbock* can be exported to various formats for downstream data analysis.

## OME-TIFF

To export images to OME-TIFF, with channel names determined by the panel file:

    steinbock export ome

The exported OME-TIFF files are generated by [xtiff](https://github.com/BodenmillerGroup/xtiff); the default destination directory is `ome`.

## histoCAT

To export images and masks to a folder structure compatible with [histoCAT for MATLAB](https://bodenmillergroup.github.io/histoCAT/):

    steinbock export histocat

This will create a histoCAT-compatible folder structure (defaults to `histocat`), with one subfolder per image, where each subfolder contains one image file per channel. Additionally, if masks are available, each image subfolder contains a single mask file.

## CSV

To export specified object data from all images as a single .csv file:

    steinbock export csv intensities regionprops -o objects.csv

This will collect object data from the `intensities` and `regionprops` directories and create a single object data table in [object data format](../file-types.md#object-data), with an additional first column indicating the source image.

## FCS

To export specified object data from all images as a single .fcs file:

    steinbock export fcs intensities regionprops -o objects.fcs

This will collect object data from the `intensities` and `regionprops` directories and create a single FCS file using the [fcswrite](https://github.com/ZELLMECHANIK-DRESDEN/fcswrite) package.

## AnnData

To export specified object data to [AnnData](https://github.com/theislab/anndata):

    steinbock export anndata --intensities intensities --data regionprops --neighbors neighbors -o objects.h5ad

This will generate a single .h5ad file, with object intensities as main data, object regionprops as observation annotations, and neighbors as pairwise observation annotations (adjacency matrix in `adj`, distances in `dists`).

!!! note "AnnData file format"
    To export the data as .loom or .zarr, specify `--format loom` or `--format zarr`, respectively.

    Currently, the .h5ad format does not allow for storing panel/image metadata, see [issue #66](https://github.com/BodenmillerGroup/steinbock/issues/66).

!!! note "Multiple data sources"
    The `--data` option can be specified multiple times to include different object data as observation annotationss.

## Graphs

To export neighbors as spatial object graphs, with object data as node attributes:

    steinbock export graphs --data intensities

By default, this will generate one .graphml file per graph using the [networkx](https://networkx.org) Python package, with object intensities as node attributes. The default destination directory is `graphs`.

!!! note "NetworkX file format"
    To export the graphs as .gexf or .gml, specify `--format gexf` or `--format gml`, respectively.

!!! note "Multiple graph attributes sources"
    The `--data` option can be specified multiple times to include different object data as graph attributes.
