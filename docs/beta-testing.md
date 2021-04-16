# Beta testing

Instructions for testing this pipeline with [TestData](https://github.com/BodenmillerGroup/TestData)

!!! danger
    The steinbock framework is in beta stage. Use at own risk.

!!! note
    Commands beginning with a hashtag symbol (`#`) are optional.

## Installation

[Install Docker](https://docs.docker.com/get-docker/)

Pull the steinbock Docker container:

    docker pull jwindhager/steinbock:0.2.0

### System configuration (Linux/MacOS)

Specify and create the data directory:

    export DATA="/mnt/data/steinbock"  # adapt accordingly
    mkdir -p "${DATA}"

For convenience, create an alias for running the steinbock Docker container:

    alias steinbock="docker run -v \"${DATA}\":/data -v /tmp/.X11-unix -v ~/.Xauthority:/root/.Xauthority:ro -e DISPLAY jwindhager/steinbock:0.2.0"

If necessary, allow the Docker container to run graphical user interfaces:

    # this is unsafe!
    xhost +local:root

Check whether steinbock runs:

    steinbock

### System configuration (Windows)

!!! danger "Experimental feature"
    Running steinbock on Windows platforms is not recommended

In the following instructions, instead of calling `steinbock`, type:

    docker run -v "D:\steinbock":/data jwindhager/steinbock:0.2.0

Adapt the path to your data directory (`"D:\steinbock"` in the above example) accordingly.

!!! note
    Commands that launch a graphical user interface (e.g. for Ilastik, CellProfiler) will not work on Windows hosts. It is recommended to run these programs directly on the Windows host, if graphical user interfaces are required.

## Data preparation

Copy the [raw data](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData/raw) to `$DATA/raw`

Copy the [panel.csv](https://github.com/BodenmillerGroup/TestData/blob/main/datasets/210308_ImcTestData/panel.csv) to `$DATA/raw`

## Data preprocessing

Convert .mcd/.txt files to .tiff and filter hot pixels:

    steinbock preprocess imc --hpf 50

This will save images to `$DATA/img` and create the steinbock panel file (`$DATA/panel.csv`).

## Pixel classification

Scale images, extract crops and prepare an Ilastik project:

    steinbock classify ilastik prepare --cropsize 50 --seed 123

This will create an Ilastik pixel classification project (`$DATA/pixel_classifier.ilp`), extract 50x50 image crops for training (`$DATA/ilastik_crops`), and prepare images for processing (`$DATA/ilastik_img`). The created images and crops only contain channels enabled in `$DATA/panel.csv` and additionaly contain the mean of all channels as first channel.

Usually, one would now interactively train the created pixel classifier using Ilastik:

    # steinbock tools ilastik

Instead, to use the pre-trained classifier:
  
  1. Replace `$DATA/pixel_classifier.ilp` with [ilastik.ilp](https://github.com/BodenmillerGroup/TestData/blob/main/datasets/210308_ImcTestData/ilastik.ilp) (rename to `pixel_classifier.ilp`)
  
  2. Replace the contents of `$DATA/ilastik_crops` with the contents of [ilastik](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData/analysis/ilastik) (optional)
  
  3. Run `steinbock classify ilastik fix` to establish compatibility with steinbock

The last operation will in-place modify the Ilastik pixel classification project and the image crops after creating a backup of these files (`.bak` file/directory extension).

Now we are ready to run the pixel classification batch:

    steinbock classify ilastik run

This will create probability images in `$DATA/ilastik_probabilities`, with color code:

- Red: Nucleus
- Green: Cytoplasm
- Blue: Background

## Cell segmentation

Prepare a CellProfiler segmentation pipeline:

    steinbock segment cellprofiler prepare

This will create a CellProfiler segmentation pipeline `$DATA/pixel_classifier.ilp`.

Interactively adapt the created pipeline as needed using the graphical CellProfiler interface:

    # steinbock tools cellprofiler

Now we are ready to run the cell segmentation batch:

    steinbock segment cellprofiler run

This will create cell masks in `$DATA/masks` (0: Background, other values: unique cell IDs).

## Single-cell data extraction

Extract mean cell intensities per channel:

    steinbock measure cells intensities

This will store cell intensities in `$DATA/cell_intensities` (one file per image).

Extract spatial cell properties ("regionprops"):

    steinbock measure cells regionprops

This will store the default cell regionprops in `$DATA/cell_regionprops` (one file per image).

Collect cell intensities and regionprops from all images into one file:

    steinbock measure cells collect

This will create the file `$DATA/cells.csv` containing all cells from all images.

## Spatial cell graph construction

Extract Euclidean distances between cell borders:

    steinbock measure dists border
    # steinbock measure dists centroid

This will create cell distance matrices in `$DATA/cell_distances` (one file per image).

Construct undirected cell graphs by theresholding on cell border distances:

    steinbock measure graphs dist --thres 4
    # steinbock measure graphs knn --k 5

This will create cell graphs (saved as edge lists) in `$DATA/cell_graphs` (one file per image).
