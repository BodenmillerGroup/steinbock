# Object measurement

In this step, object-level (e.g. single-cell) data will be extracted from segmented images.

Various types of data can be extracted, each of which is described in the following.

!!! note "Collecting multiple object data from multiple images"
    To collect all object data (e.g. intensities, region properties) from all images into a single file, see [Data export](export.md#object-data).

## Object intensities

To extract mean object intensities per channel:

    steinbock measure intensities

This will create object data tables in CSV format (see [File types](../file-types.md#object-data), one file per image). The default destination directory is `intensities`.

!!! note "Pixel aggregation"
    By default, pixels belonging to an object are aggregated by taking the mean. To specify a different [numpy](https://numpy.org) function for aggregation, use the `--aggr` option (e.g. specify `--aggr median` to measure "median object intensities").

## Region properties

To extract spatial object properties ("region properties"):

    steinbock measure regionprops

This will create object data tables in CSV format (see [File types](../file-types.md#object-data), one file per image). The default destination directory is `regionprops`.

!!! note "Region property selection"
    By default, the following [scikit-image region properties](https://scikit-image.org/docs/dev/api/skimage.measure.html#skimage.measure.regionprops) will be computed:

      - `area`
      - `centroid`
      - `major_axis_length`
      - `minor_axis_length`
      - `eccentricity`

    An alternative selection of scikit-image region properties can be specified in the `regionprops` command, e.g.:

        steinbock measure regionprops area convex_area perimeter

## Object neighbors

Neighbors can be measured (i.e., identified) based on distances between object centroids or object borders, or by pixel expansion. For distance-based neighbor identification, the maximum distance and/or number of neighbors can be specified.

!!! note "Spatial object graphs"
    Pairs of neighbors can be represented as edges on a spatial object graph, where each cell is a vertex (node), and neighboring cells are connected by an edge associated with a spatial distance.

The following commands will create directed edge lists in CSV format (see [File types](../file-types.md#object-neighbors), one file per image). For undirected graphs, i.e., graphs constructed by distance thresholding/pixel expansion, each edge will appear twice. The default destination directory is `neighbors`.

### Centroid distances

To find neighbors by thresholding on distances between object centroids:

    steinbock measure neighbors --type centroids --dmax 15

To construct k-nearest neighbor (kNN) graphs based on object centroid distances:

    steinbock measure neighbors --type centroids --kmax 5

!!! note "Distance metric"
    By default, the Euclidean distance distance is used. Other metrics can be specified using the `--metric` option, e.g.:

        steinbock measure neighbors --type centroids --dmax 15 --metric cityblock

    Available distance metrics are listed in the [documentation for scipy.spatial.distance.pdist](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.pdist.html).

!!! note "Distance-thresholded kNN graphs"
    The options `--dmax` and `--kmax` options can be combined to construct distance-thresholded kNN graphs, e.g.:
    
        steinbock measure neighbors --type centroids --dmax 15 --kmax 5

### Border distances

To find neighbors by thresholding on Euclidean distances between object borders:

    steinbock measure neighbors --type borders --dmax 4

To construct k-nearest neighbor (kNN) graphs based on Euclidean object border distances:

    steinbock measure neighbors --type borders --kmax 5 --dmax 20

!!! note "Computational complexity"
    The construction of spatial kNN graphs based on Euclidean distances between object borders is computationally expensive. To speed up the computation, always specify a suitable `--dmax` value like in the example above.

### Pixel expansion

To find neighbors by Euclidean pixel expansion (morphological dilation):

    steinbock measure neighbors --type expansion --dmax 4

!!! note "Pixel expansion versus border distances"
    Neighbor identification by pixel expansion is a special case of finding neighbors based on Euclidean distances between object borders, in which, after pixel expansion, only *touching* objects (i.e., objects within a 4-neighborhood) are considered neighbors.

## CellProfiler (legacy)

!!! danger "Legacy operation"
    The output of this operation is not actively supported by downstream processing steps.

### Pipeline preparation

To prepare a CellProfiler measurement pipeline:

    steinbock measure cellprofiler prepare

!!! note "Data/working directory"
    Within the container, your data/working directory containing the CellProfiler pipeline is accessible under `/data`.

By default, this will create a CellProfiler pipeline file `cell_measurement.cppipe` and collect all images and masks (both in 16-bit unsigned integer format) into the `cellprofiler_input` directory.

!!! note "CellProfiler plugins"
    The generated CellProfiler pipeline makes use of [custom plugins for multi-channel images](https://github.com/BodenmillerGroup/ImcPluginsCP), which are pre-installed in the *steinbock* Docker container. It can be inspected using CellProfiler as described in the following section.

### Modifying the pipeline

To interactively inspect, modify and run the pipeline, import it in CellProfiler (see [Apps](apps.md#cellprofiler)):

    steinbock apps cellprofiler

More detailed instructions on how to create CellProfiler pipelines can be found [here](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.1.3/help/pipelines_building.html).

### Batch processing

After the pipeline has been configured, it can be applied to a batch of images and masks:

    steinbock measure cellprofiler run

By default, this will generate (undocumented and unstandardized) CellProfiler output as configured in the pipeline and store it in the `cellprofiler_output` directory.
