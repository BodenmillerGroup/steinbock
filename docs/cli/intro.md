# Introduction

The following sections document the usage of the *steinbock* command-line interface (CLI).

!!! note "Prerequisites"
    From this point onwards, it is assumed that the `steinbock` command alias was [configured](../install-docker.md) correctly. To make efficient use of the *steinbock* Docker container, basic command line skills are absolutely required. Furthermore, understanding key concepts of containerization using Docker may be helpful in resolving issues.

## Trying it out

To try out *steinbock*, the [IMC mock dataset](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData) can be used as follows:

  1. Copy the [raw](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData/raw) directory to your *steinbock* data/working directory
  2. Place the [panel.csv](https://github.com/BodenmillerGroup/TestData/blob/main/datasets/210308_ImcTestData/panel.csv) into the `raw` directory in your *steinbock* data/working directory
  3. Continue with [Imaging Mass Cytometry (IMC) preprocessing](preprocessing.md#imaging-mass-cytometry-imc) and subsequent steps

!!! note
    Existing Ilastik training data ([Ilastik pixel classification project](https://github.com/BodenmillerGroup/TestData/blob/main/datasets/210308_ImcTestData/ilastik.ilp), [Ilastik crops](https://github.com/BodenmillerGroup/TestData/tree/main/datasets/210308_ImcTestData/analysis/ilastik)) can be used for testing the classification step.

## Getting help

At any time, use the `--help` option to show help about a *steinbock* command, e.g.:

    > steinbock --help

    Usage: steinbock [OPTIONS] COMMAND [ARGS]...

    Options:
    --version  Show the version and exit.
    --help     Show this message and exit.

    Commands:
    preprocess  Extract and preprocess images from raw data
    classify    Perform pixel classification to extract probabilities
    segment     Perform image segmentation to create object masks
    measure     Extract object data from segmented images
    export      Export data to third-party formats
    utils       Various utilities and tools
    view        View image using napari GUI
    apps        Third-party applications

!!! note "Directory structure"
    Unless specified otherwise, all *steinbock* commands adhere to the default [directory structure](../directories.md).

For bug reports or further help, please do not hesitate to reach out via [GitHub Issues/Discussions](https://github.com/BodenmillerGroup/steinbock).
