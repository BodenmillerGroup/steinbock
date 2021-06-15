# Object measurement

In this step, object-level (e.g., single-cell) data will be extracted from segmented images.

Various types of data can be extracted, each of which is described in the following.

## Object data

The commands below will create object data tables in CSV format (see [File types](../specs/file-types.md#object-data), one file per image). The default destination directory paths are mentioned in brackets.

!!! note "Collecting object data"
    To collect all object data from all images into a single file, see [Data export](export.md#object-data).

### Intensities

To extract mean object intensities per channel (`intensities`):

    steinbock measure intensities

!!! note "Pixel aggregation"
    By default, pixels belonging to an object are aggregated by taking the mean. To specify a different [numpy](https://numpy.org) function for aggregation, use the `--aggr` option (e.g., specify `--aggr median` to measure "median object intensities").

### Region properties

To extract spatial object properties ("region properties", `regionprops`):

    steinbock measure regionprops

!!! note "Region property selection"
    By default, the following [scikit-image region properties](https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.regionprops) will be computed:

      - `area`
      - `centroid`
      - `major_axis_length`
      - `minor_axis_length`
      - `eccentricity`

    An alternative selection of scikit-image region properties can be specified in the `regionprops` command, e.g.:

        steinbock measure regionprops area convex_area perimeter

## Object distances

To measure the pairwise Euclidean distances between object centroids:

    steinbock measure distances centroids

To measure the pairwise Euclidean distances between object borders:

    steinbock measure distances borders

The above commands will create symmetric object pixel distance matrices in CSV format (see [File types](../specs/file-types.md#object-distances), one file per image). The default destination directory is `distances`.

!!! danger "Computational complexity"
    For `n` objects, the operations in this section require the computation and storage of `n choose 2` distances.

    Computationally, calculating the pairwise Euclidean distances between cell borders is particularly expensive.

## Spatial object graphs

!!! note "Distance requirements"
    The commands in this section require object distances to be pre-computed (see previous section).

To construct spatial object graphs by thresholding on object distances (undirected):

    steinbock measure graphs --dmax 4

To construct spatial k-nearest neighbor (kNN) object graphs (directed):

    steinbock measure graphs --kmax 5

The above commands will create directed edge lists in CSV format (see [File types](../specs/file-types.md#spatial-object-graphs), one file per image). The default destination directory is `graphs`.

!!! note "Distance-thresholded kNN graphs"
    The options `--dmax` and `--kmax` can be combined to construct distance-thresholded kNN graphs.

## CellProfiler (legacy)

!!! danger "Legacy operation"
    The output of this operation is not actively supported by downstream processing steps.

### Pipeline preparation

To prepare a CellProfiler measurement pipeline:

    steinbock measure cellprofiler prepare

!!! note "Data/working directory"
    Within the container, your data/working directory containing the CellProfiler pipeline is accessible under `/data`.

By default, this will create a CellProfiler pipeline file `cell_measurement.cppipe` and collect all images and masks into the `cellprofiler_input` directory.

!!! note "CellProfiler plugins"
    The generated CellProfiler pipeline makes use of [custom plugins for multi-channel images](https://github.com/BodenmillerGroup/ImcPluginsCP), which are pre-installed in the *steinbock* Docker container. It can be inspected using CellProfiler as described in the following section.

### Modifying the pipeline

To interactively inspect, modify and run the pipeline, open it in CellProfiler (see [Apps](apps.md#cellprofiler)):

    steinbock apps cellprofiler

More detailed instructions on how to create CellProfiler pipelines can be found [here](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.1.3/help/pipelines_building.html).

### Batch processing

After the pipeline has been configured, it can be applied to a batch of images and masks:

    steinbock measure cellprofiler run

By default, this will generate (undocumented and unstandardized) CellProfiler output as configured in the pipeline and store it in the `cellprofiler_output` directory.
