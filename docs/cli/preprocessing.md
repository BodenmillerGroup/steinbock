# Preprocessing

In this step, image data will be prepared for processing with *steinbock*.

Various sources for raw data are supported by *steinbock*, each of which is described in the following. If you miss support for an imaging modality, please consider [filing an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues).

!!! note "Optional preprocessing"
    The *steinbock* framework natively supports input images saved in Tag Image File Format (TIFF), see [File types](../file-types.md#images). If you already have preprocessed TIFF files, you can directly use those for further processing. If you have preprocessed images in another file format supported by [imageio](https://imageio.readthedocs.io), you need to convert them to *steinbock*-compatible TIFF files first, see [External images](#external-images).

!!! note "Computational resources"
    Unless specified otherwise, *steinbock* converts all input images to 32-bit floating point images upon loading, see [File types](../file-types.md#images). For large images, this may exhaust a system's available random access memory (RAM). In these situations, it is recommended to run all operations on image tiles, see [mosaics](utils.md#mosaics).

## Imaging Mass Cytometry (IMC)

Preprocessing of IMC data consists of two steps:

  1. Create a *steinbock* panel file and, optionally, edit it to select channels
  2. Extract images from .mcd/.txt files according to the created *steinbock* panel file

!!! note "Panel-based image extraction"
    The *steinbock* panel determines the presence and order of channels in the extracted images.

### Panel creation

A *steinbock* panel file contains information about the channels in an image, such as channel ID (e.g. metal tag), channel name (e.g. antibody target), or whether a channel will be used in certain tasks (e.g. classification, segmentation). Multiple options exist for creating a *steinbock* panel file for IMC applications:

  - Manual *steinbock* panel file creation, following the [*steinbock* panel format specification](../file-types.md#panel)
  - Automatic *steinbock* panel file creation from metadata embedded in raw MCD/TXT files
  - Conversion from an "IMC panel file" in *IMC Segmentation Pipeline*[^1] format (undocumented)

!!! note "Panel file types"
    The *steinbock* panel file is different from the "IMC panel file" used in the original *IMC Segmentation Pipeline*[^1] in that it is ordered (i.e., the channel order in the panel matches the channel order in the images) and only requires `channel` and `name` columns (see [File types](../file-types.md#panel)). By default, channels in a *steinbock* panel file generated from IMC raw data are sorted by mass. As the *steinbock* panel format allows for further arbitrary columns, unmapped columns from an original "IMC panel" will be "passed through" to the generated *steinbock* panel.

When manually creating the *steinbock* panel file, no further actions are required; proceed with image conversion. Otherwise, to create a *steinbock* panel file for IMC data processing:

    steinbock preprocess imc panel

This will create a *steinbock* panel at the specified location (defaults to `panel.csv`) as follows:

  - If an IMC panel file (in *IMC Segmentation Pipeline*[^1] format, undocumented) exists at the specified location (defaults to `raw/panel.csv`), it is converted to the [*steinbock* panel format](../file-types.md#panel).
  - If no IMC panel file was found, the *steinbock* panel is created based on all acquisitions in all .mcd files found at the specified location (defaults to `raw`). 
  - If no IMC panel file and no .mcd file were found, the *steinbock* panel is created based on all .txt files found at the specified location (defaults to `raw`).

!!! note "Different panels"
    In principle, IMC supports acquiring a different panel for each .mcd/.txt file and acquisition. When creating a *steinbock* panel from .mcd/.txt files, the created panel will contain all targets found in any of the input files. During image conversion (see below), only targets marked as `keep=1` in the panel file will be retained; imaging data with missing channels (identified by the `channel` column in the panel file) are skipped.

### Image conversion

To convert .mcd/.txt files in the raw data directory to TIFF and filter hot pixels:

    steinbock preprocess imc images --hpf 50

This will extract images from raw files (source directory defaults to `raw`) and save them at the specified location (defaults to `img`). Each image corresponds to one acquisition in one file, with the image channels filtered (`keep` column) and sorted according to the *steinbock* panel file at the specified location (defaults to `panel.csv`). For corrupted .mcd files, *steinbock* will try to recover the missing acquisitions from matching .txt files. In a second step, images from *unmatched* .txt files are extracted as well.

Furthermore, this commands also creates an image information table as described in [File types](../file-types.md#image-information). In addition to the default columns, the following IMC-specific columns will be added:

  - `source_file`: the raw .mcd/.txt file name
  - `recovery_file`: the corresponding .txt file name, if available
  - `recovered`: *True* if the .mcd acquisition was recovered from the corresponding .txt file
  - Acquisition-specific information: 
    - `acquisition_id`: numeric acquisition ID
    - `acquisition_description`: user-specified acquisition description
    - `acquisition_posx_um`, `acquisition_posy_um`: start position, in micrometers
    - `acquisition_width_um`, `acquisition_height_um`: dimensions, in micrometers

!!! note "IMC file matching"
    Matching of .txt files to .mcd files is performed by file name: If a .txt file name starts with the file name of an .mcd file (without extension) AND ends with `_{acquisition}.txt`, where `{acquisition}` is the numeric acquisition ID, it is considered matching that particular acquisition from the .mcd file.

!!! note "ZIP archives"
    If .zip archives are found in the raw data directory, contained .txt/.mcd files will be automatically extracted to a temporary directory, unless disabled using the `--no-unzip` command-line option. After image extraction, this temporary directory and its contents will be removed.

After image extraction, if the `--hpf` option is specified, the images are filtered for hot pixels. The value of the `--hpf` option (`50` in the example above) determines the *hot pixel filtering threshold*.

!!! note "Hot pixel filtering"
    Hot pixel filtering works by comparing each pixel to its 8-neighborhood (i.e., neighboring pixels at a [Chebyshev distance](https://en.wikipedia.org/wiki/Chebyshev_distance) of 1). If the difference (not: absolute difference) between the pixel and any of its 8 neighbor pixels exceeds a *hot pixel filtering threshold*, the pixel is set to the maximum neighbor pixel value ("hot pixel-filtered"). In the original implementation of the *IMC Segmentation Pipeline*[^1], a *hot pixel filtering threshold* of 50 is recommended.

[^1]: Zanotelli et al. ImcSegmentationPipeline: A pixel classification-based multiplexed image segmentation pipeline. Zenodo, 2017. DOI: [10.5281/zenodo.3841961](https://doi.org/10.5281/zenodo.3841961).

## External images

*External images* are images preprocessed externally (i.e., without *steinbock*) that are saved in an image format supported by [imageio](https://imageio.readthedocs.io).

For convenience, to create a template panel file based on external image data stored at the specified location (defaults to `external`):

    steinbock preprocess external panel

To convert external image data to *steinbock*-supported TIFF files (see [File types](../file-types.md#images)) and save them to the specified location (defaults to `external`):

    steinbock preprocess external images
