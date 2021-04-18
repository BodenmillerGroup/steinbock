# Welcome

*steinbock* is a framework for processing multi-channel images to extract single-cell data.

## Overview

The *steinbock* framework comprises the following components:

- The [*steinbock* Python package](https://github.com/BodenmillerGroup/steinbock) with the integrated *steinbock* command-line interface
- The [*steinbock* Docker container](https://hub.docker.com/r/jwindhager/steinbock), exposing the *steinbock* command-line interface, with supported third-party software (e.g., Ilastik, CellProfiler) pre-installed

It is extensible and supports any **pixel classification-based image segmentation** workflow.

At its core, pixel classification-based image segmentation comprises the following steps:

  1. **Preprocessing**: extract images from raw data for processing

  2. **Pixel classification**: probabilistically assign a class to each pixel

  3. **Cell segmentation**: use the assigned class probabilities to define cells

  4. **Measurement**: extract single-cell data from segmented cells

!!! note "Semantic cell segmentation"
    This workflow describes a *semantic segmentation* approach. Unlike *instance segmentation*, the classification step does not inherently separate instances (e.g., cells) and therefore needs a segmentation step for instance separation.

!!! note "Segmenting arbitrary regions"
    While this documentation assumes the task of cell segmentation, the presented concepts can be generalized to arbitrary definitions of regions ("segments") by replacing the terminology where necessary (e.g., "cell" --> "region").

Currently, the following workflows are implemented:

  - **[Standard workflow]** Zanotelli et al. ImcSegmentationPipeline: A pixel classification-based multiplexed image segmentation pipeline. Zenodo, 2017. DOI: [10.5281/zenodo.3841961](https://doi.org/10.5281/zenodo.3841961).

## Resources

Code: [https://github.com/BodenmillerGroup/steinbock](https://github.com/BodenmillerGroup/steinbock)

Documentation: [https://bodenmillergroup.github.io/steinbock](https://bodenmillergroup.github.io/steinbock)

Issue tracker: [https://github.com/BodenmillerGroup/steinbock/issues](https://github.com/BodenmillerGroup/steinbock/issues)

DockerHub repository: [https://hub.docker.com/r/jwindhager/steinbock](https://hub.docker.com/r/jwindhager/steinbock)

## Authors

- [Jonas Windhager](mailto:jonas.windhager@uzh.ch) (main author)

## Contributing

Pull requests are welcome. Please make sure to update documentation as appropriate.

For major changes, please open an issue first to discuss what you would like to change.
