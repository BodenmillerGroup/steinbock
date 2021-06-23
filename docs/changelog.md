# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.5.4] - 2021-06-23

  - Speed up Ilastik image creation


## [0.5.3] - 2021-06-22

  - Fix CSV/FCS export


## [0.5.2] - 2021-06-15

  - Fix networkx node attribute export
  - Remove `object_` prefix from default directory names
  - Speed up intensity measurement (use scipy.ndimage for aggregation)


## [0.5.1] - 2021-06-10

  - Version bumps of tifffile, xtiff
  - Preprocessing/postprocessing parameter support for DeepCell


## [0.5.0] - 2021-06-03

  - Module restructuring
  - PyPI package release
  - CLI refactoring, --version option
  - Improved documentation (API documentation is w.i.p.)
  - Export to OME-TIFF, CSV, FCS, AnnData, graph file formats
  - Match related files by name rather than alphabetical order
  - Customizable pixel/channel aggregation strategies
  - [Many more](https://github.com/BodenmillerGroup/steinbock/compare/v0.4.0...v0.5.0) small bug fixes & improvements


## [0.4.0] - 2021-05-27

  - Python API cleanup
  - Added DeepCell segmentation support


## [0.3.7] - 2021-05-20

  - Automatic SCM versioning
  - Steinbock version file checks
  - Renamed steinbock panel columns
  - Improved Docker container Python package setup
  - Combined kNN/distance-thresholded graph generation


## [0.3.6] - 2021-04-29

  - Make panel channel label values optional
  - Rename panel columns metal, name to id, label


## [0.3.5] - 2021-04-29

  - Minor bug fixes and performance improvements
  - Separated IMC panel/image preprocessing to allow for easier channel filtering


## [0.3.4] - 2021-04-27

  - [#6](https://github.com/BodenmillerGroup/steinbock/issues/6) Panel creation from .mcd/.txt files
  - [#9](https://github.com/BodenmillerGroup/steinbock/issues/9) Improved documentation on Ilastik feature selection
  - [#10](https://github.com/BodenmillerGroup/steinbock/issues/10) Fixed Ilastik class label colors
  - [#11](https://github.com/BodenmillerGroup/steinbock/issues/11) Simplified command-line interface


## [0.3.3] - 2021-04-21

New functionality, bug fixes, documentation improvements

Added:

  - ZIP archive support for IMC data (closes [#2](https://github.com/BodenmillerGroup/steinbock/issues/2))
  - Ilastik channel ordering & grouping (closes [#3](https://github.com/BodenmillerGroup/steinbock/issues/3))
  - Run container as non-privileged user (fixes [#4](https://github.com/BodenmillerGroup/steinbock/issues/4))


## [0.3.2] - 2021-04-19

New functionality, bug fixes, documentation improvements

Added:

  - Mask matching
  - IMC panel pass-through
  - Generalized object segmentation
  - Hardened image loading to allow for tiles of size 1 in one dimension


## [0.3.1] - 2021-04-18

Documentation, minor improvements, fix memory leaks & stitching


## [0.3.0] - 2021-04-16

CLI refactoring, mosaic tooling


## [0.2.0] - 2021-04-12

CLI refactoring, removed imctoolkit dependency

Added:

  - Support for "raw" IMC panels
  - Additional user input validation
  - Mean channel in Ilastik images/crops
  - Additional progress bars/indicators
  - Measurements for cell regionprops
  - Measurements for cell distances/graphs


## [0.1.0] - 2021-04-08

Initial release for beta testing


[0.5.4]: https://github.com/BodenmillerGroup/steinbock/compare/v0.5.3...v0.5.4
[0.5.3]: https://github.com/BodenmillerGroup/steinbock/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/BodenmillerGroup/steinbock/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/BodenmillerGroup/steinbock/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.3.7...v0.4.0
[0.3.7]: https://github.com/BodenmillerGroup/steinbock/compare/v0.3.6...v0.3.7
[0.3.6]: https://github.com/BodenmillerGroup/steinbock/compare/v0.3.5...v0.3.6
[0.3.5]: https://github.com/BodenmillerGroup/steinbock/compare/v0.3.4...v0.3.5
[0.3.4]: https://github.com/BodenmillerGroup/steinbock/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/BodenmillerGroup/steinbock/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/BodenmillerGroup/steinbock/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/BodenmillerGroup/steinbock/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/BodenmillerGroup/steinbock/releases/tag/v0.1.0
