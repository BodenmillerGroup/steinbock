from pathlib import Path

import click
import click_log

from ..._cli.utils import OrderedClickGroup, catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import cellpose, train

cellpose_cli_available = cellpose.cellpose_available


@click.group(
    name="train",
    cls=OrderedClickGroup,
    help="Train a cellpose model using labeled data",
)
def train_cmd_group():
    pass


@train_cmd_group.command(name="run", help="Train a cellpose model using labeled data")
#model specification parameters
@click.option(
    "--gpu",
    "gpu",
    default=False,
    show_default=True,
    help="whether or not to save model to GPU, will check if GPU available",
)
@click.option(
    "--model_type",
    "model_type",
    type=click.Choice(
        [
            "nuclei",
            "cyto",
            "cyto2",
            "tissuenet",
            "livecell",
            "CP",
            "CPx",
            "TN1",
            "TN2",
            "TN3",
            "LC1",
            "LC2",
            "LC3",
            "LC4",
        ]
    ),
    default="tissuenet",
    show_default=True,
    help="any model that is available in the GUI, use name in GUI e.g. ‘livecell’ (can be user-trained or model zoo)",
)
@click.option(
    "--pretrained_model",
    "pretrained_model",
    default=None,
    show_default=True,
    help="cellpose pretrained model to use as start for training",
)
@click.option(
    "--net_avg",
    "net_avg",
    default=True,
    show_default=True,
    help=" loads the 4 built-in networks and averages them if True, loads one network if False",
)
@click.option(
    "--diam_mean",
    "diam_mean",
    default=30.0,
    type=float,
    help="mean diameter to resize cells to during training -- if starting from pretrained models it cannot be changed from 30.0",
)
@click.option(
    "--device",
    "device",
    default=None,
    help="device used for model running / training (torch.device(‘cuda’) or torch.device(‘cpu’)), overrides gpu input, recommended if you want to use a specific GPU (e.g. torch.device(‘cuda:1’))",
)
@click.option(
    "--residual_on",
    "residual_on",
    default=True,
    help=" use 4 conv blocks with skip connections per layer instead of 2 conv blocks like conventional u-nets",
)
@click.option(
    "--style_on",
    "style_on",
    default=True,
    help="use skip connections from style vector to all upsampling layers",
)
@click.option(
    "--concatenation",
    "concatenation",
    default=False,
    help="if True, concatentate downsampling block outputs with upsampling block inputs; default is to add",
)


# #training parameters
@click.option(
    "--train_data",
    "train_data",
    default="cellpose_crops",
    required=True,
    help="folder containing training data ",
)
@click.option(
    "--train_labels",
    "train_labels",
    default="cellpose_masks",
    help="folder containing masks corresponding to images in training_data",
)
@click.option(
    "--train_files",
    "train_files",
    default=None,
    type=str,
    help="provide training data as a list of files",
)
@click.option(
    "--test_data",
    "test_data",
    default=None,
    help="images for testing",
)
@click.option(
    "--test_labels",
    "test_labels",
    default=None,
    help="labels for test_data, where 0=no masks; 1,2,…=mask labels; can include flows as additional images",
)
@click.option(
    "--test_files",
    "test_files",
    default=None,
    help="file names for images in test_data (to save flows for future runs)",
)
@click.option(
    "--channels",
    "channels",
    default=[1, 2],
    type=list,
    help="channels to use for training",
)
@click.option(
    "--normalize",
    "normalize",
    default=True,
    type= bool,
    help="normalize data so 0.0=1st percentile and 1.0=99th percentile of image intensities in each channel",
)
@click.option(
    "--save_path",
    "save_path",
    default="training_out",
    help="where to save trained model, if None it is not saved",
)
@click.option(
    "--save_every",
    "save_every",
    default=50,
    type=click.INT,
    help="ave network every [save_every] epochs",
)
@click.option(
    "--learning_rate",
    "learning_rate",
    default=0.1,
    help="learning rate. Default: %(default)s",
)
@click.option(
    "--n_epochs",
    "n_epochs",
    default=1,
    help="how many times to go through whole training set during training",
)
@click.option(
    "--weight_decay",
    "weight_decay",
    default=0.0001,
    help="weight decay",
)
@click.option(
    "--momentum",
    "momentum",
    default=0.9,
    help="not explaied in cellpose API documentation",
)
@click.option(
    "--SGD",
    "SGD",
    default=True,
    help="use SGD as optimization instead of RAdam",
)
@click.option(
    "--batch_size",
    "batch_size",
    default=8,
    help="minimum number of images to train on per epoch, with a small training set (< 8 images) it may help to set to 8",
)
@click.option(
    "--nimg_per_epoch",
    "nimg_per_epoch",
    default=None,
    type=click.INT,
    help="minimum number of images to train on per epoch, with a small training set (< 8 images) it may help to set to 8",
)
@click.option(
    "--rescale",
    "rescale",
    default=True,
    help="whether or not to rescale images to diam_mean during training, if True it assumes you will fit a size model after training or resize your images accordingly, if False it will try to train the model to be scale-invariant (works worse)",
)
@click.option(
    "--min_train_masks",
    "min_train_masks",
    default=5,
    type=click.INT,
    help="minimum number of masks an image must have to use in training set",
)
@click.option(
    "--model_name",
    "model_name",
    default=None,
    type=str,
    help="minimum number of masks an image must have to use in training set",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def train_run_cmd(
    gpu,
    pretrained_model,
    model_type,
    net_avg,
    diam_mean,
    device,
    residual_on,
    style_on,
    concatenation,

    train_data,
    train_labels,
    train_files,
    test_data,
    test_labels,
    test_files,
    channels,
    normalize,
    save_path,
    save_every,
    learning_rate,
    n_epochs,
    weight_decay,
    momentum,
    SGD,
    batch_size,
    nimg_per_epoch,
    rescale,
    min_train_masks,
    model_name


):
    Path("cellpose_crops").mkdir(exist_ok=True)
    Path("masks").mkdir(exist_ok=True)
    Path("training_out").mkdir(exist_ok=True)
    model_file = train.try_train_model(
        #model initiation parameters
        gpu = gpu,
        pretrained_model = pretrained_model,
        model_type = model_type,
        net_avg = net_avg,
        diam_mean = diam_mean,
        device=device,
        residual_on=residual_on,
        style_on= style_on,
        concatenation=concatenation,

        #training parameters
        train_data = train_data,
        train_labels = train_labels,
        train_files=train_files,
        test_data=test_data,
        test_labels=test_labels,
        test_files=test_files,
        channels=channels,
        normalize=normalize,
        save_path=save_path,
        save_every=save_every,
        learning_rate=learning_rate,
        n_epochs=n_epochs,
        weight_decay=weight_decay,
        momentum=momentum,
        SGD=SGD,
        batch_size=batch_size,
        nimg_per_epoch=nimg_per_epoch,
        rescale=rescale,
        min_train_masks=min_train_masks,
        model_name=model_name
    )
    print(f"The trained model file can be found here: {model_file}")
    logger.info(model_file)


@train_cmd_group.command(
    name="prepare", help="Generate images and masks for training a cellpose model"
)
@click.option(
    "--pretrained_model",
    "pretrained_model",
    default=None,
    type=str,
    # show_default=True,
    help="cellpose pretrained model to use as start for training",
)
@click.option(
    "--cropsize",
    "cellpose_crop_size",
    type=click.INT,
    default=500,
    show_default=True,
    help="Cellpose crop size (in pixels)",
)
@click.option(
    "--input_data",
    "input_data",
    default="img",
    type=str,
    required=True,
    help="folder containing training data ",
)
@click.option(
    "--cellpose_crops",
    "cellpose_crops",
    default="cellpose_crops",
    type=str,
    required=True,
    help="Destination for ellpose training crops",
)
@click.option(
    "--cellpose_masks",
    "cellpose_masks",
    default="cellpose_masks",
    type=str,
    required=True,
    help="Destination for cellpose training crops",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel file",
)
@click.option(
    "--model_type",
    "model_type",
    type=click.Choice(
        [
            "nuclei",
            "cyto",
            "cyto2",
            "tissuenet",
            "livecell",
            "CP",
            "CPx",
            "TN1",
            "TN2",
            "TN3",
            "LC1",
            "LC2",
            "LC3",
            "LC4",
        ]
    ),
    default="tissuenet",
    show_default=True,
    help="any model that is available in the GUI, use name in GUI e.g. ‘livecell’ (can be user-trained or model zoo)",
)
@click.option(
    "--pretrained_model",
    "pretrained_model",
    default=None,
    show_default=True,
    help="cellpose pretrained model to use as start for training",
)
@click.option(
    "--net_avg",
    "net_avg",
    default=True,
    show_default=True,
    help=" loads the 4 built-in networks and averages them if True, loads one network if False",
)
@click.option(
    "--diam_mean",
    "diam_mean",
    default=30.0,
    type=float,
    help="mean diameter to resize cells to during training -- if starting from pretrained models it cannot be changed from 30.0",
)
@click.option(
    "--device",
    "device",
    default=None,
    help="device used for model running / training (torch.device(‘cuda’) or torch.device(‘cpu’)), overrides gpu input, recommended if you want to use a specific GPU (e.g. torch.device(‘cuda:1’))",
)
@click.option(
    "--residual_on",
    "residual_on",
    default=True,
    help=" use 4 conv blocks with skip connections per layer instead of 2 conv blocks like conventional u-nets",
)
@click.option(
    "--style_on",
    "style_on",
    default=True,
    help="use skip connections from style vector to all upsampling layers",
)
@click.option(
    "--concatenation",
    "concatenation",
    default=False,
    help="if True, concatentate downsampling block outputs with upsampling block inputs; default is to add",
)






@click.option(
    "--gpu",
    "gpu",
    default=False,
    show_default=True,
    help="whether or not to save model to GPU, will check if GPU available",
)

@click.option(
    "--batch-size",
    "batch_size",
    type=click.INT,
    default=8,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--normalize/--no-normalize",
    "normalize",
    default=True,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--diameter",
    "diameter",
    type=click.FLOAT,
    help="See Cellpose documentation",
)
@click.option(
    "--tile/--no-tile",
    "tile",
    default=False,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--tile-overlap",
    "tile_overlap",
    type=click.FLOAT,
    default=0.1,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--resample/--no-resample",
    "resample",
    default=True,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--interp/--no-interp",
    "interp",
    default=True,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--flow-threshold",
    "flow_threshold",
    type=click.FLOAT,
    default=0.4,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--cellprob_threshold",
    "cellprob_threshold",
    type=click.FLOAT,
    default=0.0,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--min-size",
    "min_size",
    type=click.INT,
    default=15,
    show_default=True,
    help="See Cellpose documentation",
)


@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def train_prepare_cmd(
    input_data,
    cellpose_crops,
    cellpose_masks,
    panel_file,
    cellpose_crop_size,
    #model initiation
    gpu,
    pretrained_model,
    model_type,
    net_avg,
    diam_mean,
    device,
    residual_on,
    style_on,
    concatenation,

    #segmentation
    batch_size,
    normalize,
    diameter,
    tile,
    tile_overlap,
    resample,
    interp,
    flow_threshold,
    cellprob_threshold,
    min_size,



):
    # os.mkdir("cellpose_crops")
    Path("cellpose_crops").mkdir(exist_ok=True)
    Path("masks").mkdir(exist_ok=True)
    Path("training_out").mkdir(exist_ok=True)

    crop_loc, mask_loc = train.prepare_training(
        input_data = input_data,
        cellpose_crops = cellpose_crops,
        cellpose_masks = cellpose_masks,
        panel_file = panel_file,
        cellpose_crop_size = cellpose_crop_size,

        #model parameters
        gpu = gpu,
        pretrained_model = pretrained_model,
        model_type = model_type,
        net_avg = net_avg,
        diam_mean = diam_mean,
        device = device,
        residual_on = residual_on,
        style_on = style_on,
        concatenation = concatenation,

        #segmentation parameters
        batch_size = batch_size,
        normalize = normalize,
        diameter = diameter,
        tile = tile,
        tile_overlap = tile_overlap,
        resample = resample,
        interp = interp,
        flow_threshold = flow_threshold,
        cellprob_threshold = cellprob_threshold,
        min_size = min_size,





    )
    print(f"Cellpose traing crops in: {crop_loc}")
    print(f"Cellpose traing masks in {mask_loc}")
    # logger.info(model_file)
