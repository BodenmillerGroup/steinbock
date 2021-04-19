# File types

## Panel

File extension: `.csv`

User-provided list of channels present in the images (in order)

Comma-separated values (CSV) file with column headers and no index

| Column | Description | Type | Required? |
| --- | --- | --- | --- |
| `name` | Channel name (e.g., antibody target) | Text | yes |
| `ilastik` | Use this channel for pixel classification using Ilastik | Boolean (0/1) | no |

The *steinbock* panel allows for further arbitrary columns.

## Images

File extension: `.tiff`

Multi-channel images, where each channel corresponds to a panel entry

Tag Image File Format (TIFF) images of any data type in CYX dimension order

!!! note "Image data type"
    Unless explicitly mentioned, images are converted to 32-bit floating point upon loading (without rescaling).

## Probabilities

File extension: `.tiff`

Color images, with one color per class encoding the probability of pixels belonging to that class

16-bit unsigned integer TIFF images in YXS dimension order, same YX shape as source image

!!! danger "Probability image size"
    The size of probability images may be different from the original images (see [Ilastik pixel classification workflow](../cli/classification.md#ilastik)).

## Object masks

File extension: `.tiff`

Grayscale image, with one unique value per object ("object ID", 0 for background)

16-bit unsigned integer TIFF images in YX dimension order, same YX shape as source image

## Object data

File extension: `.csv`

Object measurements (e.g., mean intensities, morphological features)

CSV file with feature/channel name as column and object IDs as index

!!! note "Combined object data"
    For data containing measurements from multiple images, a combined index of image name and object ID is used.

## Object distances

File extension: `.csv`

Pixel distances between objects (e.g., Euclidean centroid distances)

Symmetric CSV file (one per image) with object IDs as both column and index

## Spatial object graphs

File extension: `.csv`

List of directed edges defining a spatial object neighborhood graph

CSV file (one per image) with two columns (`Object1`, `Object2`) and no index

Each row defines an edge from object with ID `Object1` to object with ID `Object2`

!!! note "Undirected graphs"
    For undirected graphs, each edge appears twice (one edge per direction)
