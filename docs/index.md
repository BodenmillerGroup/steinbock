# Home

Documentation will be made available upon request


## Beta testing instructions

Instructions for testing this pipeline with [TestData](https://github.com/BodenmillerGroup/TestData)

### Installation

[Install Docker](https://docs.docker.com/get-docker/)

Pull the steinbock Docker container:

    docker pull jwindhager/steinbock:0.1.0

Specify and create the data/working directory:

    export DATA="/mnt/data"  # adapt accordingly
    mkdir -p "${DATA}"

For convenience, create an alias for running the steinbock Docker container:

    alias steinbock="docker run -v \"${DATA}\":/data -v /tmp/.X11-unix:/tmp/.X11-unix -v ~/.Xauthority:/root/.Xauthority:ro -e DISPLAY jwindhager/steinbock"

Allow the Docker container to run graphical user interfaces:

    xhost +local:root  # this is unsafe!

Check whether steinbock runs:

    steinbock

### Data preparation

Copy the [raw data](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData/raw) to `$DATA/raw`

Create the following `$DATA/panel.csv` file:

    channel,name,keep,ilastik
    1,Laminin,1,1
    2,H3K27Ac,1,1
    3,Cytokeratin 5,1,1
    4,YBX1,1,1
    5,Ag107,0,0

### Data preprocessing

Convert .mcd/.txt files to .tiff and filter hot pixels:

    steinbock preprocess imc --hpf 50

### Pixel classification

Scale images, extract patches and prepare an Ilastik project:

    steinbock classify ilastik prepare --patchsize 50 --seed 123

Usually, one would now interactively train a pixel classifier using ilastik:

    # steinbock classify ilastik app

Instead, to use the pre-trained classifier:
  
  1. Replace `$DATA/pixel_classifier.ilp` with [ilastik.ilp](https://github.com/BodenmillerGroup/TestData/blob/main/datasets/210308_ImcTestData/ilastik.ilp) (rename to `pixel_classifier.ilp`)
  
  2. Replace the contents of `$DATA/ilastik_patches` with the contents of [ilastik](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData/analysis/ilastik) (optional)
  
  3. Run `steinbock classify ilastik fix` to patch the provided files

Perform the pixel classification batch:

    steinbock classify ilastik run

### Cell segmentation

Prepare a CellProfiler segmentation pipeline:

    steinbock segment cellprofiler prepare

Optionally, interactively edit the pipeline:

    # steinbock segment cellprofiler app

Perform the cell segmentation batch:

    steinbock segment cellprofiler run

Optionally, measure cells using CellProfiler (legacy approach):

    # steinbock segment cellprofiler prepare-measure
    # steinbock segment cellprofiler app  # to edit pipeline
    # steinbock segment cellprofiler run-measure

### Single-cell data extraction

Extract mean cell intensities per channel (one file per image):

    steinbock measure intensities

Collect cell intensities from all images into one file:

    steinbock measure collect

### Spatial cell graph construction

Extract Euclidean distances between cell borders:

    steinbock measure border-dists
    # steinbock measure centroid-dists

Construct undirected cell graphs by theresholding on cell border distances:

    steinbock graphs dist --thres 4
    # steinbock graphs knn --k 5
