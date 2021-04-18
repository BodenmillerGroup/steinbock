# Cell segmentation

In this step, given the probabilities from the pixel classification step, cells will be segmented.

This will result in grayscale *cell masks* of the same x/y dimensions as the input images containing unique pixel values for each cell (cell IDs) and `0` for background (see [file types](/specs/file-types/)).

Various approaches are supported by steinbock, each of which is described in the following.

## CellProfiler

[CellProfiler](https://cellprofiler.org) is an open-source software for measuring and analyzing cell images. Here, CellProfiler is used for nucleus detection and region growth-based cell segmentation.

### Pipeline preparation

In a first step, a CellProfiler pipeline is prepared for processing the images:

    steinbock segment cellprofiler prepare

By default, this will create a CellProfiler pipeline file `cell_segmentation.cppipe`.

!!! note "The CellProfiler pipeline"
    The generated CellProfiler pipeline makes use of [custom plugins for multi-channel images](https://github.com/BodenmillerGroup/ImcPluginsCP), which are pre-installed in the *steinbock* Docker container. It can be inspected using CellProfiler as described in the following section.    

### Modifying the pipeline

To interactively inspect, modify and run the pipeline, open it in CellProfiler (see [tools](/cli/tools/#cellprofiler)):

    steinbock tools cellprofiler

More detailed instructions on how to create CellProfiler pipelines can be found [here](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.1.3/help/pipelines_building.html).

!!! note "CellProfiler output"
    By default, the pipeline is configured to generate cell masks as grayscale 16-bit unsigned integer TIFF images with the same name and x/y dimensions as the input images (see [file types](/specs/file-types/)). In custom segmentation scenarios, this convention should be followed to ensure compatibility with downstream measurement tasks.

!!! danger "Segmentation parameters"
    Segmentation using CellProfiler is highly customizable and sensitive to parameter choices. The default parameter values may not be suitable in all cases and parameter values require careful tuning for each dataset.

### Batch processing

After the pipeline has been configured, it can be applied to a batch of probability images:

    steinbock segment cellprofiler run

This will create cell masks of the same x/y dimensions as the input images containing unique pixel values for each cell (cell IDs) and `0` for background (see [file types](/specs/file-types/)). The default destination directory for these images is `masks`.
