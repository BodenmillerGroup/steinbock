# Object measurement

In this step, object-level (e.g., single-cell) data will be extracted from segmented images.

Various types of data can be extracted, each of which is described in the following.

## Object data

To extract mean object intensities per channel (`object_intensities`):

    steinbock measure intensities

To extract spatial object properties ("region properties", `object_regionprops`):

    steinbock measure regionprops

!!! note "Region properties"
    By default, the following [scikit-image region properties](https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.regionprops) will be computed:

      - `area`
      - `centroid`
      - `major_axis_length`
      - `minor_axis_length`
      - `eccentricity`

    An alternative selection of [scikit-image region properties](https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.regionprops) can be specified in the `regionprops` command, e.g.:

        steinbock measure regionprops area convex_area perimeter

The above commands will create object data tables in CSV format (see [file types](../specs/file-types.md#object-data), one file per image). The default destination directory paths are mentioned in brackets above.

!!! note "Collecting object data"
    To collect all object data from all images into a single file, see [data collection](tools.md#data-collection).

## Object distances

To measure the pairwise Euclidean distances between object centroids:

    steinbock measure dists centroid

To measure the pairwise Euclidean distances between object borders:

    steinbock measure dists border

The above commands will create symmetric object pixel distance matrices in CSV format (see [file types](../specs/file-types.md#object-distances), one file per image). The default destination directory is `object_dists`.

!!! danger "Computational complexity"
    For `n` objects, the operations in this section require the computation and storage of `n choose 2` distances.

    In particular, computing the pairwise Euclidean distances between cell borders is computationally expensive.

## Spatial object graphs

!!! note "Distance requirements"
    The commands in this section require object distances to be pre-computed (see previous section).

To construct spatial object graphs by thresholding on object distances (undirected):

    steinbock measure graphs dist --thres 4

To construct spatial k-nearest neighbor (kNN) object graphs (directed):

    steinbock measure graphs knn --k 5

The above commands will create directed edge lists in CSV format (see [file types](../specs/file-types.md#spatial-object-graphs), one file per image). The default destination directory is `object_graphs`.

## CellProfiler (legacy)

!!! danger "Legacy operation"
    The output of this operation will not be actively supported by future downstream analysis workflows.

### Pipeline preparation

To prepare a CellProfiler measurement pipeline:

    steinbock measure cellprofiler prepare

!!! note "Data/working directory"
    Within the container, your data/working directory containing the CellProfiler pipeline is accessible under `/data`.

By default, this will create a CellProfiler pipeline file `cell_measurement.cppipe` and collect all images and masks into the `cellprofiler_input` directory.

!!! note "CellProfiler plugins"
    The generated CellProfiler pipeline makes use of [custom plugins for multi-channel images](https://github.com/BodenmillerGroup/ImcPluginsCP), which are pre-installed in the *steinbock* Docker container. It can be inspected using CellProfiler as described in the following section.

### Modifying the pipeline

To interactively inspect, modify and run the pipeline, open it in CellProfiler (see [tools](tools.md#cellprofiler)):

    steinbock tools cellprofiler

More detailed instructions on how to create CellProfiler pipelines can be found [here](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.1.3/help/pipelines_building.html).

### Batch processing

After the pipeline has been configured, it can be applied to a batch of images and masks:

    steinbock measure cellprofiler run

By default, this will generate (undocumented and unstandardized) CellProfiler output as configured in the pipeline and store it in the `cellprofiler_output` directory.