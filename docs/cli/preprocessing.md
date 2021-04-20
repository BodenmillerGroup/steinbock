# Preprocessing

In this step, image data is prepared for processing with *steinbock*.

Various data sources are supported, each of which is described in the following.

If you miss support for an imaging modality, please consider [filing an issue on GitHub](https://github.com/BodenmillerGroup/steinbock/issues).

!!! note "Optional preprocessing"
    Not all raw data require preprocessing. The *steinbock* framework natively supports input images saved in Tag Image File Format (TIFF), see [file types](../specs/file-types.md#images). If your images are available in TIFF already, preprocessing is optional.

!!! note "Computational resources"
    Unless specified otherwise, *steinbock* converts all input images to 32-bit floating point images upon loading, see [file types](../specs/file-types.md#images). For large images, this may exhaust a system's available random access memory (RAM). In these situations, it is recommended to run all operations on image tiles, see [mosaics](tools.md#mosaics).

## Imaging Mass Cytometry (IMC)

To convert .mcd/.txt files in the raw data directory to TIFF and filter hot pixels:

    steinbock preprocess imc --hpf 50

This will first try to extract images from the .mcd files (one image per acquisition). For corrupted .mcd files, it will try to locate the matching .txt files from which to recover the missing acquisition data. In a second step, images from *unmatched* .txt files are extracted as well.

!!! note "IMC file matching"
    Matching of .txt files to .mcd files is performed by file name: If a .txt file name starts with the file name of an .mcd file (without extension) AND ends with `_{acquisition}.txt`, where `{acquisition}` is an existing acquisition ID, it is considered matching that particular acquisition from the .mcd file.

After image extraction, if the `--hpf` option is specified, the images are filtered for hot pixels. The value of `--hpf` (50 in the example above) determines the *hot pixel filtering threshold*. In the original implementation of the IMC segmentation pipeline[^1], a value of 50 is recommended.

!!! note "Hot pixel filtering"
    Hot pixel filtering works by comparing each pixel to its 8-neighborhood (i.e., neighboring pixels at a [Chebyshev distance](https://en.wikipedia.org/wiki/Chebyshev_distance) of 1). If the difference between the pixel and any of its 8 neighbor pixels exceeds the *hot pixel filtering threshold*, the pixel is set to the maximum neighbor pixel value ("hot pixel-filtered").

Finally, the images and a *steinbock* panel file are stored at the specified destination paths (defaults to the `img` directory and the `panel.csv` file in the *steinbock* data/working directory).

!!! note "Panel files"
    The *steinbock* panel file is different from the original panel file in that it is ordered (i.e., the channel order in the panel matches the channel order in the images), only contains entries for channels present in the preprocessed images, and only requires a `name` column (but allows for arbitrary columns, see [file types](../specs/file-types.md#panel)). Therefore, the *steinbock* panel generated from the original IMC panel as shown here will "pass through" all columns except the `full` column.

[^1]: Zanotelli et al. ImcSegmentationPipeline: A pixel classification-based multiplexed image segmentation pipeline. Zenodo, 2017. DOI: [10.5281/zenodo.3841961](https://doi.org/10.5281/zenodo.3841961).
