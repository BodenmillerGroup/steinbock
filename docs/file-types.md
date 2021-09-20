# File types

## Panel

File extension: .csv

User-provided list of channels present in the images (in order)

Comma-separated values (CSV) file with column headers and no index

| Column | Description | Type | Required? |
| --- | --- | --- | --- |
| `channel` | Unique channel ID, e.g. metal isotope | Text | yes |
| `name` | Unique channel name, e.g. antibody target<br>(can be empty only for rows with `keep=0`) | Text or empty | yes |
| `keep` | Whether the channel is present in preprocessed images<br>(if column is absent, all channels are assumed present) | Boolean (`0` or `1`) | no |
| `ilastik` | Group label for creating [*steinbock* Ilastik images](cli/classification.md#ilastik)<br>(if column is absent, all channels are used separately) | Numeric or empty | no |
| `deepcell` | Group label for [DeepCell segmentation](cli/segmentation.md#deepcell)<br>(if column is absent, all channels are used separately) | Numeric or empty | no |

The *steinbock* panel allows for further arbitrary columns.

## Images

File extension: .tiff

Multi-channel images, where each channel corresponds to a panel entry

Tag Image File Format (TIFF) images of any data type in CYX dimension order

!!! note "Image data type"
    Unless explicitly mentioned, images are converted to 32-bit floating point upon loading (without rescaling).

## Image information

File extension: .csv

Image information (e.g. image dimensions) extracted during preprocessing

CSV file with image file name as index (`Image` column) and the following columns:

| Column | Description | Type |
| --- | --- | --- |
| `image` | Unique image file name | Text |
| `width_px` | Image width, in pixels | Numeric |
| `height_px` | Image height, in pixels | Numeric |
| `num_channels` | Number of image channels | Numeric |

Further columns may be added by [modality-specific preprocessing commands](cli/preprocessing.md).


## Probabilities

File extension: .tiff

Color images, with one color per class encoding the probability of pixels belonging to that class

16-bit unsigned integer TIFF images in YXS dimension order, same YX ratio as source image

!!! danger "Probability image size"
    The size of probability images may be different from the original images (see [Ilastik pixel classification](cli/classification.md#ilastik)).

## Object masks

File extension: .tiff

Grayscale images, with one unique value per object ("object ID", 0 for background)

16-bit unsigned integer TIFF images in YX dimension order, same YX shape as source image

## Object data

File extension: .csv

Object measurements (e.g. mean intensities, morphological features)

CSV file with object IDs as index (`Object` column) and feature/channel names as columns

!!! note "Combined object data"
    For data containing measurements from multiple images, a combined index of image name and object ID is used.

## Object neighbors

File extension: .csv

List of directed edges defining a spatial object neighborhood graph

CSV file (one per image) with no index and three columns (`Object`, `Neighbor`, `Distance`)

!!! note "Undirected graphs"
    For undirected graphs, each edge appears twice (one edge per direction)
