# Preprocessing

In this step, image data will be prepared for processing with *steinbock*.

Various data sources are supported, each of which is described in the following.

If you miss support for an imaging modality, please consider [filing an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues).

!!! note "Optional preprocessing"
    Not all raw data require preprocessing. The *steinbock* framework natively supports input images saved in Tag Image File Format (TIFF), see [file types](../specs/file-types.md#images). If your images are available in TIFF already, preprocessing is optional.

!!! note "Computational resources"
    Unless specified otherwise, *steinbock* converts all input images to 32-bit floating point images upon loading, see [file types](../specs/file-types.md#images). For large images, this may exhaust a system's available random access memory (RAM). In these situations, it is recommended to run all operations on image tiles, see [mosaics](tools.md#mosaics).

## Imaging Mass Cytometry (IMC)

To convert .mcd/.txt files in the raw data directory to TIFF and filter hot pixels:

    steinbock preprocess imc --hpf 50

This will extract images from .mcd files (one image per acquisition, channels sorted by mass). For corrupted .mcd files, it will try to locate the matching .txt files from which to recover the missing acquisition. In a second step, images from *unmatched* .txt files are extracted as well.

!!! note "ZIP archives"
    If .zip archives are found in the raw data directory, contained .txt/.mcd files will be automatically extracted to a temporary directory, unless disabled using the `--no-unzip` command-line option. After image extraction, this temporary directory and its contents will be removed.

!!! note "IMC file matching"
    Matching of .txt files to .mcd files is performed by file name: If a .txt file name starts with the file name of an .mcd file (without extension) AND ends with `_{acquisition}.txt`, where `{acquisition}` is an existing acquisition ID, it is considered matching that particular acquisition from the .mcd file.

After image extraction, if the `--hpf` option is specified, the images are filtered for hot pixels. The value of `--hpf` (50 in the example above) determines the *hot pixel filtering threshold*. In the original implementation of the IMC segmentation pipeline[^1], a value of 50 is recommended.

!!! note "Hot pixel filtering"
    Hot pixel filtering works by comparing each pixel to its 8-neighborhood (i.e., neighboring pixels at a [Chebyshev distance](https://en.wikipedia.org/wiki/Chebyshev_distance) of 1). If the difference between the pixel and any of its 8 neighbor pixels exceeds the *hot pixel filtering threshold*, the pixel is set to the maximum neighbor pixel value ("hot pixel-filtered").

Finally, the images are saved (default: `img`) and a *steinbock* panel file is created as follows: 

  1. If an IMC panel file exists at the specified location (default: `raw/panel.csv`), it is converted to the [*steinbock* panel format](../specs/file-types.md#panel) and saved at the specified location (default: `panel.csv`).
  2. If no such file exists, the panel is created based on the first acquisition in the first .mcd file. 
  3. If no .mcd file was found, the panel is created based on the first .txt file.

!!! note "Panel files"
    The *steinbock* panel file is different from the IMC panel file used in the original IMC segmentation pipeline in that it is ordered (i.e., the channel order in the panel matches the channel order in the images), only contains entries for channels present in the preprocessed images, and only requires a `name` column. As the *steinbock* panel format allows for further arbitrary columns (see [file types](../specs/file-types.md#panel)), a *steinbock* panel generated from an original IMC panel will contain all original columns ("column pass-through") except the `full` column.

[^1]: Zanotelli et al. ImcSegmentationPipeline: A pixel classification-based multiplexed image segmentation pipeline. Zenodo, 2017. DOI: [10.5281/zenodo.3841961](https://doi.org/10.5281/zenodo.3841961).
