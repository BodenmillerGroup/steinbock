# Measurement

In this step, cell-level data will be extracted from segmented images.

Various types of data can be extracted, each of which is described in the following.

## Single-cell data

To extract mean cell intensities per channel (`cell_intensities`):

    steinbock measure cells intensities

To extract default spatial cell properties ("region properties", `cell_regionprops`):

    steinbock measure cells regionprops

The above commands will create cell tables in CSV format (see [file types](/specs/file-types/), one file per image). The default destination directory paths are mentioned in brackets above.

To collect all cell data from all images into a single file:

    steinbock measure collect cell_intensities cell_regionprops

This will create a single cell table in CSV format with the first (additional) column indicating the source image (see [file types](/specs/file-types/)). The default destination file is `cells.csv`. The arguments to the `collect` command are the directories from where to collect the cell data.

## Cell-cell distances

!!! note "Computational complexity"
    For `n` cells, the operations in this section require the computation and storage of `n choose 2` distances

To measure the pairwise Euclidean distances between cell centroids:

    steinbock measure dists centroid

To measure the pairwise Euclidean distances between cell borders:

    steinbock measure dists border

!!! danger "Computational complexity"
    Computing the pairwise Euclidean distances between cell borders is computationally expensive.

The above commands will create symmetric cell pixel distance matrices in CSV format (see [file types](/specs/file-types/), one file per image). The default destination directory is `cell_distances`.

## Spatial cell graphs

!!! note "Distance requirements"
    The commands in this section require cell-cell distances to be pre-computed (see previous section).

To construct spatial cell graphs by thresholding on cell-cell distances (undirected):

    steinbock measure graphs dist --thres 4

To construct spatial k-nearest neighbor (kNN) cell graphs (directed):

    steinbock measure graphs knn --k 5

The above commands will create directed edge lists in CSV format (see [file types](/specs/file-types/), one file per image). The default destination directory is `cell_graphs`.

## CellProfiler (legacy)

!!! danger "Legacy operation"
    The output of this operation will not be actively supported by future downstream analysis workflows.

### Pipeline preparation

To prepare a CellProfiler measurement pipeline:

    steinbock measure cellprofiler prepare

By default, this will create a CellProfiler pipeline file `cell_measurement.cppipe` and collect all images and masks into the `cellprofiler_input` directory.

!!! note "The CellProfiler pipeline"
    The generated CellProfiler pipeline makes use of [custom plugins for multi-channel images](https://github.com/BodenmillerGroup/ImcPluginsCP), which are pre-installed in the *steinbock* Docker container. It can be inspected using CellProfiler as described in the following section.

### Modifying the pipeline

To interactively inspect, modify and run the pipeline, open it in CellProfiler (see [tools](/cli/tools/#cellprofiler)):

    steinbock tools cellprofiler

More detailed instructions on how to create CellProfiler pipelines can be found [here](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.1.3/help/pipelines_building.html).

### Batch processing

After the pipeline has been configured, it can be applied to a batch of images and masks:

    steinbock measure cellprofiler run

By default, this will generate (undocumented and unstandardized) CellProfiler output as configured in the pipeline and store it in the `cellprofiler_output` directory.