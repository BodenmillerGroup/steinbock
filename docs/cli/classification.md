# Pixel classification

In this step, for each image, the probabilities of pixels belonging to a given class (e.g., Nucleus, Cytoplasm, Background) will be determined. This will result in *probability images* with one color per class encoding the probability of pixels belonging to that class (see [file types](../specs/file-types.md#probabilities)).

Various approaches are supported by *steinbock*, each of which is described in the following.

## Ilastik

[Ilastik](https://www.ilastik.org) is an application for interactive learning and segmentation. Here, the semantic [pixel classification](https://www.ilastik.org/documentation/pixelclassification/pixelclassification) workflow of Ilastik is used to perform pixel classification using random forests.

### Data preparation

In a first step, input data are prepared for processing with Ilastik:

    steinbock classify ilastik prepare --cropsize 50 --seed 123

With default desination file/directory paths shown in brackets, this will:

  - aggregate, scale and convert images to *steinbock* Ilastik format (`ilastik_img`)
  - extract and save one random crop of 50x50 pixels per image for training (`ilastik_crops`)
  - create a default *steinbock* Ilastik pixel classification project file (`pixel_classifier.ilp`)

!!! note "Ilastik image data"
    All generated image data are saved in *steinbock* Ilastik HDF5 format (undocumented). 
    
    If an `ilastik` column is present in the *steinbock* panel file, channels are sorted and grouped according to the corresponding values in that column: For each image, each group of channels is aggregated by computing the mean along the channel axis ("mean channel image"); channels without a group label are ignored. The generated images consist of one channel per group. In addition, the mean of all included channels is prepended to the generated images as an additional channel, unless `--no-mean` is specified.
    
    Furthermore, all generated image data is scaled two-fold in x and y, unless specified otherwise using the `--scale` command-line option. This helps with more accurately identifying object borders in segmentation workflows for images of relatively low resolution (e.g., Imaging Mass Cytometry). In applications with higher resolution (e.g., sequential immunofluorescence), it is recommended to not scale the image data, i.e., specify `--scale 1`.

### Training the classifier

To interactively train a new classifier, open the pixel classification project in Ilastik (see [tools](tools.md#ilastik)):

    steinbock tools ilastik

More detailed instructions on how to use Ilastik for training a pixel classifier can be found [here](https://www.ilastik.org/documentation/pixelclassification/pixelclassification).

!!! note "Class labels"
    By default, the Ilastik pixel classification project is configured for training three classes (Nucleus, Cytoplasm, Background) for cell segmentation workflows. Different numbers of classes and class labels may be preferred for other use cases (e.g., two classes for Tumor/Stroma-segmentation). While the number and order of classes is arbitrary and can be changed by the user, it needs to be compatible with downstream [segmentation steps](segmentation.md).

!!! note "Feature selection"
    The choice of features in Ilastik's feature selection step depends on the input data. For relatively small IMC datasets, the selection of all default features greater than or equal to 1 pixel is recommended (see [here](https://github.com/BodenmillerGroup/ImcSegmentationPipeline/blob/main/scripts/imc_preprocessing.ipynb)).

### Existing training data

!!! danger "Experimental feature"
    Reusing existing training data is an experimental feature. Use at own risk. Always make backups of your data.

Instead of training a new classifier, one can use an existing classifier by

  - replacing the generated Ilastik pixel classification project file with a pre-trained project, and

  - replacing the image crops (see [data preparation](#data-preparation)) with the crops originally used for training.

Subsequently, to ensure compatibility of the external Ilastik project file/crops:

    steinbock classify ilastik fix

This will attempt to in-place patch the Ilastik pixel classification project and the image crops after creating a backup (`.bak` file/directory extension), unless `--no-backup` is specified.

!!! note "Patching existing training data"
    This command will convert image crops to 32-bit floating point images with CYX dimension order and save them in *steinbock* Ilastik HDF5 format (undocumented). It will then adjust the metadata in the Ilastik project file accordingly.

### Batch processing

After training the pixel classifier on the image crops (or providing and patching a pre-trained one), it can be applied to a batch of full-size images created in the [data preparation](#data-preparation) step as follows:

    steinbock classify ilastik run

By default, this will create probability images in `ilastik_probabilities`, with one color per class encoding the probability of pixels belonging to that class (see [file types](../specs/file-types.md#probabilities)).

!!! note "Probability images"
    The size of the generated probability images are equal to the size of the Ilastik input images, i.e., scaled by a user-specified factor that defaults to two (see above). Make sure to adapt downstream segmentation workflows accordingly to create object masks matching the original (i.e., unscaled) images.

    If the default three-class structure is used, the probability images are RGB images with the following color code:

      - <span style="color: red;">R</span>: Nuclei
      - <span style="color: green;">G</span>: Cytoplasm
      - <span style="color: blue;">B</span>: Background