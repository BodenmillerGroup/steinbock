<img src="img/steinbock-logo.png" align="right" alt="Logo" width="150" />

# Welcome

*steinbock* is a framework for multi-channel image processing

The *steinbock* framework comprises the following components:

- The [*steinbock* Python package](https://pypi.org/project/steinbock) with the integrated *steinbock command-line interface* (CLI)
- The [*steinbock* Docker container](https://github.com/BodenmillerGroup/steinbock/pkgs/container/steinbock) interactively exposing the *steinbock* command-line interface, with supported third-party software (e.g. Ilastik, CellProfiler) pre-installed

!!! note "Modes of usage"
    *steinbock* can be used [interactively](cli/intro.md) as well as [programmatically](python/intro.md) from within Python scripts.

## Overview

At its core, *steinbock* provides the following functionality:

  - Image preprocessing, including utilities for tiling/stitching images
  - Pixel classification, to enable pixel classification-based image segmentation
  - Image segmentation, to identify objects (e.g. cells or other regions of interest)
  - Object measurement, to extract single-cell data, cell neighbors, etc.
  - Data export, to facilitate downstream data analysis

While all *steinbock* functionality can be used in a modular fashion, the framework was designed for - and explicitly supports - the following image segmentation workflows:

 - **[Random forest-based object segmentation]** Zanotelli et al. ImcSegmentationPipeline: A pixel classification-based multiplexed image segmentation pipeline. Zenodo, 2017. DOI: [10.5281/zenodo.3841961](https://doi.org/10.5281/zenodo.3841961).
 - **[Deep learning-based cell segmentation]** Greenwald et al. Whole-cell segmentation of tissue images with human-level performance using large-scale data annotation and deep learning. Nature, 2021. DOI: [10.1038/s41587-021-01094-0](https://doi.org/10.1038/s41587-021-01094-0).

 The *steinbock* framework is extensible and support for further workflows may be added in the future. If you are missing support for a workflow, please consider [filing an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues).

## Resources

Code: [https://github.com/BodenmillerGroup/steinbock](https://github.com/BodenmillerGroup/steinbock)

Documentation: [https://bodenmillergroup.github.io/steinbock](https://bodenmillergroup.github.io/steinbock)

Issue tracker: [https://github.com/BodenmillerGroup/steinbock/issues](https://github.com/BodenmillerGroup/steinbock/issues)

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
