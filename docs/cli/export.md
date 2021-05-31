# Data export

## Object data

### Data collection

To collect all object data from all images into a single file:

    steinbock export data csv object_intensities object_regionprops

This will create a single object data table in CSV format with the first column indicating the source image (see [file types](../specs/file-types.md#object-data)). The default destination file is `objects.csv`. The arguments to the `collect` command are the directories from where to collect the object data.
