# Preprocessing

In this step, image data will be prepared for processing with *steinbock*.

Various sources for raw data are supported by *steinbock*, each of which is described in the following. If you miss support for an imaging modality, please consider [filing an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues).

!!! note "Optional preprocessing"
    Not all raw data require preprocessing. The *steinbock* framework natively supports input images saved in Tag Image File Format (TIFF), see [File types](../specs/file-types.md#images). If your images are available in TIFF already, preprocessing may not be required.

!!! note "Computational resources"
    Unless specified otherwise, *steinbock* converts all input images to 32-bit floating point images upon loading, see [File types](../specs/file-types.md#images). For large images, this may exhaust a system's available random access memory (RAM). In these situations, it is recommended to run all operations on image tiles, see [mosaics](tools.md#mosaics).

## Imaging Mass Cytometry (IMC)

Preprocessing of IMC data consists of two steps:

  1. Create a *steinbock* panel file and, optionally, edit it to select channels
  2. Extract images from .mcd/.txt files according to the created *steinbock* panel file

!!! note "Panel-based image extraction"
    The *steinbock* panel determines the presence and order of channels in the extracted images.

### Panel generation

To create a *steinbock* panel file from IMC raw data:

    steinbock preprocess imc panel

This will generate a *steinbock* panel file as follows:

  - If an IMC panel file (in *IMC Segmentation Pipeline*[^1] format, undocumented) exists at the specified location (defaults to `raw/panel.csv`), it is converted to the [*steinbock* panel format](../specs/file-types.md#panel).
  - If no IMC panel file was found, the *steinbock* panel is created based on the first acquisition in the first .mcd file found at the specified location (defaults to `raw`). 
  - If no IMC panel file and no .mcd file were found, the *steinbock* panel is created based on the first .txt file found at the specified location (defaults to `raw`).

!!! note "Panel file types"
    The *steinbock* panel file is different from the IMC panel file used in the original *IMC Segmentation Pipeline*[^1] in that it is ordered (i.e., the channel order in the panel matches the channel order in the images) and only requires `channel` and `name` columns (see [File types](../specs/file-types.md#panel)). By default, channels in a *steinbock* panel file generated from IMC raw data are sorted by mass. As the *steinbock* panel format allows for further arbitrary columns, unmapped columns from an original "IMC panel" will be "passed through" to the generated *steinbock* panel.

!!! note "Manual panel file creation"
    The *steinbock* panel file can also be created manually, following the [*steinbock* panel format specification](../specs/file-types.md#panel).

### Image conversion

To convert .mcd/.txt files in the raw data directory to TIFF and filter hot pixels:

    steinbock preprocess imc images --hpf 50

This will extract images from .mcd files at the specified location (defaults to `raw`). Each image corresponds to one acquisition in one file, with the image channels filtered and sorted according to the *steinbock* panel file at the specified location (defaults to `panel.csv`). For corrupted .mcd files, *steinbock* will try to recover the missing acquisitions from matching .txt files. In a second step, images from *unmatched* .txt files are extracted as well.

!!! note "IMC file matching"
    Matching of .txt files to .mcd files is performed by file name: If a .txt file name starts with the file name of an .mcd file (without extension) AND ends with `_{acquisition}.txt`, where `{acquisition}` is the numeric acquisition ID, it is considered matching that particular acquisition from the .mcd file.

!!! note "ZIP archives"
    If .zip archives are found in the raw data directory, contained .txt/.mcd files will be automatically extracted to a temporary directory, unless disabled using the `--no-unzip` command-line option. After image extraction, this temporary directory and its contents will be removed.

After image extraction, if the `--hpf` option is specified, the images are filtered for hot pixels. The value of the `--hpf` option (`50` in the example above) determines the *hot pixel filtering threshold*.

!!! note "Hot pixel filtering"
    Hot pixel filtering works by comparing each pixel to its 8-neighborhood (i.e., neighboring pixels at a [Chebyshev distance](https://en.wikipedia.org/wiki/Chebyshev_distance) of 1). If the difference (not: absolute difference) between the pixel and any of its 8 neighbor pixels exceeds a *hot pixel filtering threshold*, the pixel is set to the maximum neighbor pixel value ("hot pixel-filtered"). In the original implementation of the *IMC Segmentation Pipeline*[^1], a *hot pixel filtering threshold* of 50 is recommended.

[^1]: Zanotelli et al. ImcSegmentationPipeline: A pixel classification-based multiplexed image segmentation pipeline. Zenodo, 2017. DOI: [10.5281/zenodo.3841961](https://doi.org/10.5281/zenodo.3841961).
