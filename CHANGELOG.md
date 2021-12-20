# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.3] - 2021-12-20

  - Fix memory issue with Ilastik image creation

## [0.10.2] - 2021-12-07

  - Fix deepcell incompatibility with scikit-image upgrade


## [0.10.1] - 2021-12-06

  - Fix AnnData export warning
  - Allow duplicated txt/mcd file names
  - Upgrade readimc and other dependencies


## [0.10.0] - 2021-11-05

  - Unified object data (csv, fcs, anndata) export commands
  - Improved anndata export: concatenation, intensities, graphs
  - Improved IMC panel preprocessing: support for different panels
  - Added functionality for importing image data using imageio
  - Clean up and upgrade dependencies, including deepcell 0.11.0
  - Change image file name pattern to make acquisitions sortable
  - Upgrade readimc for faster reading of .txt files
  - Change CellProfiler input image dtype to uint16
  - Change histoCAT mask dtype to uint16
  - Updated documentation on Docker


## [0.9.1] - 2021-10-12

  - Fixed preprocessing of IMC Segmentation Pipeline panels


## [0.9.0] - 2021-10-11

  - Upgraded dependencies
  - Improved documentation
  - Reduced Docker image size
  - Replaced imctools with readimc
  - Added dockerized unit tests (w.i.p.)
  - Restructured package, renamed tools to utils
  - Updated package information, added `all` extra
  - Added histoCAT image export command
  - Added steinbock logo (Nils Eling)


## [0.8.1] - 2021-09-22

  - Added missing deepcell column to IMC panel preprocessing from raw data


## [0.8.0] - 2021-09-21

  - Improved error handling & messages
  - Restructured & improved documentation
  - IMC preprocessing: extract image metadata
  - Fix steinbock versioning in docker container
  - Upgraded dependencies, including deepcell 0.10.0
  - Fix permission issues using fixuid approach


## [0.7.3] - 2021-09-09

  - Make container ready for passwd mounting
  - Fix OME export destination directory name


## [0.7.2] - 2021-09-09

  - Fixed graph export


## [0.7.1] - 2021-09-09

  - Renamed graph measurement to neighbor measurement


## [0.7.0] - 2021-09-01

  - Improved graph construction performance
  - Added new graph construction methods, including pixel expansion
  - Removed distance computation in favor of more performant graph construction
  - Fixed IMC panel preprocessing (unreported bugs)
  - Fixed Ilastik pixel classification (unreported bugs)


## [0.6.2] - 2021-08-21

  - Improved documentation & switched to versioned documentation
  - Improved IMC Segmentation Pipeline panel support ([#38](https://github.com/BodenmillerGroup/steinbock/issues/38))


## [0.6.1] - 2021-08-17

  - Fixed data type conversion upon image loading


## [0.6.0] - 2021-08-17

  - Updated CellProfiler and other dependencies ([#22](https://github.com/BodenmillerGroup/steinbock/issues/22))
  - Switch from Docker Hub to GitHub Container Registry ([#34](https://github.com/BodenmillerGroup/steinbock/issues/34))
  - Various compatibility improvements and bugfixes ([#21](https://github.com/BodenmillerGroup/steinbock/issues/21), [#28](https://github.com/BodenmillerGroup/steinbock/issues/28), [#32](https://github.com/BodenmillerGroup/steinbock/issues/32), [#35](https://github.com/BodenmillerGroup/steinbock/issues/35))


## [0.5.6] - 2021-06-29

  - Switch to bilinear interpolation for Ilastik mean channel
  - Make image/mask data type configurable via environment variables


## [0.5.5] - 2021-06-28

  - Fix steinbock version check
  - Add meanfactor option to Ilastik (compatibility with IMC segmentation pipeline)
  - Save Ilastik images/crops as uint16 (compatibility with IMC segmentation pipeline)


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


[0.10.3]: https://github.com/BodenmillerGroup/steinbock/compare/v0.10.2...v0.10.3
[0.10.2]: https://github.com/BodenmillerGroup/steinbock/compare/v0.10.1...v0.10.2
[0.10.1]: https://github.com/BodenmillerGroup/steinbock/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.9.1...v0.10.0
[0.9.1]: https://github.com/BodenmillerGroup/steinbock/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/BodenmillerGroup/steinbock/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.7.3...v0.8.0
[0.7.3]: https://github.com/BodenmillerGroup/steinbock/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/BodenmillerGroup/steinbock/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/BodenmillerGroup/steinbock/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.6.2...v0.7.0
[0.6.2]: https://github.com/BodenmillerGroup/steinbock/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/BodenmillerGroup/steinbock/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/BodenmillerGroup/steinbock/compare/v0.5.6...v0.6.0
[0.5.6]: https://github.com/BodenmillerGroup/steinbock/compare/v0.5.5...v0.5.6
[0.5.5]: https://github.com/BodenmillerGroup/steinbock/compare/v0.5.4...v0.5.5
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
