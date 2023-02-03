<img src="img/steinbock-logo.png" align="right" alt="Logo" width="150" />

# Welcome

*steinbock* is a toolkit for processing multiplexed tissue images

The *steinbock* toolkit comprises the following components:

- The [*steinbock* Python package](https://pypi.org/project/steinbock) with the integrated *steinbock command-line interface* (CLI)
- The [*steinbock* Docker container](https://github.com/BodenmillerGroup/steinbock/pkgs/container/steinbock) interactively exposing the *steinbock* command-line interface, with supported third-party software (e.g. Ilastik, CellProfiler) pre-installed

!!! note "Modes of usage"
    *steinbock* can be used both [interactively](cli/intro.md) using the command-line interface (CLI) and [programmatically](python/intro.md) from within Python scripts.

## Overview

At its core, *steinbock* provides the following functionality:

  - Image preprocessing, including utilities for tiling/stitching images
  - Pixel classification, to enable pixel classification-based image segmentation
  - Image segmentation, to identify objects (e.g. cells or other regions of interest)
  - Object measurement, to extract single-cell data, cell neighbors, etc.
  - Data export, to facilitate downstream data analysis
  - Visualization of multiplexed tissue images

!!! note "Downstream single-cell data analysis"
    *steinbock* is a toolkit for extracting single-cell data from multiplexed tissue images and NOT for downstream single-cell data analysis.

While all *steinbock* functionality can be used in a modular fashion, the toolkit was designed for - and explicitly supports - the following image segmentation workflows:

 - **[Ilastik/CellProfiler]** Zanotelli et al. ImcSegmentationPipeline: A pixel classification-based multiplexed image segmentation pipeline. Zenodo, 2017. DOI: [10.5281/zenodo.3841961](https://doi.org/10.5281/zenodo.3841961).
 - **[DeepCell/Mesmer]** Greenwald et al. Whole-cell segmentation of tissue images with human-level performance using large-scale data annotation and deep learning. Nature Biotechnology, 2021. DOI: [10.1038/s41587-021-01094-0](https://doi.org/10.1038/s41587-021-01094-0).
 - **[Cellpose]** Stringer et al. Cellpose: a generalist algorithm for cellular segmentation. Nature methods, 2021. DOI: [10.1038/s41592-020-01018-x](https://doi.org/10.1038/s41592-020-01018-x)

 The *steinbock* toolkit is extensible and support for further workflows may be added in the future. If you are missing support for a workflow, please consider [filing an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues).

## Resources

Code: [https://github.com/BodenmillerGroup/steinbock](https://github.com/BodenmillerGroup/steinbock)

Documentation: [https://bodenmillergroup.github.io/steinbock](https://bodenmillergroup.github.io/steinbock)

Issue tracker: [https://github.com/BodenmillerGroup/steinbock/issues](https://github.com/BodenmillerGroup/steinbock/issues)

Discussions: [https://github.com/BodenmillerGroup/steinbock/discussions](https://github.com/BodenmillerGroup/steinbock/discussions)

Workshop 2023: [https://github.com/BodenmillerGroup/ImagingWorkshop2023](https://github.com/BodenmillerGroup/ImagingWorkshop2023)

## Citing steinbock

Please cite the following paper when using *steinbock* in your work:

!!! quote
    Windhager J, Bodenmiller B, Eling N (2021). An end-to-end workflow for multiplexed image processing and analysis. bioRxiv. doi: https://doi.org/10.1101/2021.11.12.468357.

```
@article{Windhager2021,
  author = {Windhager, Jonas and Bodenmiller, Bernd and Eling, Nils},
  title = {An end-to-end workflow for multiplexed image processing and analysis},
  year = {2021},
  doi = {10.1101/2021.11.12.468357},
  URL = {https://www.biorxiv.org/content/early/2021/11/13/2021.11.12.468357},
  journal = {bioRxiv}
}
```
