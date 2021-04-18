# Introduction

The following sections document the usage of the *steinbock* command-line interface (CLI).

!!! danger "Development status"
    The *steinbock* framework is in beta stage. Use at own risk. Always make backups of your data.

## Getting help

Use the `--help` option to list all possible input parameters to a *steinbock* command, e.g.:

    > steinbock --help

    Usage: steinbock [OPTIONS] COMMAND [ARGS]...

    Options:
    --help  Show this message and exit.

    Commands:
    preprocess  Extract and preprocess images from raw data
    classify    Perform pixel classification to create probability images
    segment     Perform cell segmentation to create cell masks
    measure     Extract single-cell data from segmented cells
    tools       Various tools and applications


## Trying out

To try out *steinbock*, use the [IMC mock dataset](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData) as follows:

  1. Copy the [raw](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData/raw) directory to your *steinbock* data/working directory
  2. Place the [panel.csv](https://github.com/BodenmillerGroup/TestData/blob/main/datasets/210308_ImcTestData/panel.csv) into the `raw` directory in your *steinbock* data/working directory

!!! note
    Existing Ilastik training data ([Ilastik pixel classification project](https://github.com/BodenmillerGroup/TestData/blob/main/datasets/210308_ImcTestData/ilastik.ilp), [Ilastik crops](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData/analysis/ilastik)) can be used for the classification step.

