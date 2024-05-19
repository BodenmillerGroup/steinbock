import logging
from pathlib import Path

import click
import click_log
import numpy as np

from ... import io
from ..._cli.utils import OrderedClickGroup, catch_exception
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import cellpose

logger = logging.getLogger(__name__)

try:
    import torch

    torch_available = True
except Exception as e:
    torch_available = False

cellpose_cli_available = cellpose.cellpose_available
model_names = [
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


def float_or_none(ctx, param, value):
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        raise click.BadParameter(
            'Please provide a valid floating point number or "None".'
        )


@click.group(
    name="cellpose",
    cls=OrderedClickGroup,
    help="Use cellpose to train a model and/or run segmentaiton",
)
def cellpose_cmd_group():
    pass


@cellpose_cmd_group.command(
    name="run", help="Run an object segmentation batch using Cellpose"
)
@click.option(
    "--model",
    "model_name",
    type=click.Choice(model_names),
    default="tissuenet",
    show_default=True,
    help="Name of the Cellpose model, choose on of the 14 pretrained models available in cellpose2",
)
@click.option(
    "--pretrained-model",
    "pretrained_model",
    type=click.Path(exists=True, dir_okay=False),
    help="Full path to pretrained cellpose model(s); if not specified, no model is loaded",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--minmax/--no-minmax",
    "channelwise_minmax",
    default=False,
    show_default=True,
    help="Channel-wise min-max normalization",
)
@click.option(
    "--zscore/--no-zscore",
    "channelwise_zscore",
    default=False,
    show_default=True,
    help="Channel-wise z-score normalization",
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
    "--aggr",
    "aggr_func_name",
    type=click.STRING,
    default="mean",
    show_default=True,
    help="Numpy function for aggregating channel pixels",
)
@click.option(
    "--net-avg/--no-net-avg",
    "net_avg",
    default=True,
    show_default=True,
    help="Load the 4 built-in networks and averages them",
)
@click.option(
    "--batch-size",
    "batch_size",
    type=click.INT,
    default=8,
    show_default=True,
    help="number of 224x224 patches to run simultaneously on the GPU (can make smaller or bigger depending on GPU memory usage).",
)
@click.option(
    "--normalize/--no-normalize",
    "normalize",
    default=True,
    show_default=True,
    help="Normalize data so 0.0=1st percentile and 1.0=99th percentile of image intensities in each channel",
)
@click.option(
    "--diameter",
    "diameter",
    callback=float_or_none,
    default=30,
    show_default=True,
    help="if set to None, then diameter is automatically estimated if size model is loaded",
)
@click.option(
    "--tile/--no-tile",
    "tile",
    default=False,
    show_default=True,
    help="tiles image to ensure GPU/CPU memory usage limited (recommended)",
)
@click.option(
    "--tile-overlap",
    "tile_overlap",
    type=click.FLOAT,
    default=0.1,
    show_default=True,
    help="fraction of overlap of tiles when computing flows",
)
@click.option(
    "--resample/--no-resample",
    "resample",
    default=True,
    show_default=True,
    help="run dynamics at original image size (will be slower but create more accurate boundaries)",
)
@click.option(
    "--interp/--no-interp",
    "interp",
    default=True,
    show_default=True,
    help="interpolate during dynamics",
)
@click.option(
    "--flow-threshold",
    "flow_threshold",
    type=click.FLOAT,
    default=1,
    show_default=True,
    help="flow error threshold (all cells with errors below threshold are kept",
)
@click.option(
    "--cellprob-threshold",
    "cellprob_threshold",
    type=click.FLOAT,
    default=-6,
    show_default=True,
    help="all pixels with value above threshold kept for masks, decrease to find more and larger masks",
)
@click.option(
    "--min-size",
    "min_size",
    type=click.INT,
    default=15,
    show_default=True,
    help="minimum number of pixels per mask, can turn off with -1",
)
@click.option(
    "-o",
    "mask_dir",
    type=click.Path(file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask output directory",
)
@click.option(
    "--channels",
    "channels",
    type=str,
    help="Channels to use for training. Please provide two comma-separated integers as a string",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def run_cmd(
    pretrained_model,
    model_name: str,
    img_dir,
    channelwise_minmax,
    channelwise_zscore,
    panel_file,
    aggr_func_name,
    net_avg,
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
    mask_dir,
    channels,
):
    channel_groups = None
    if Path(panel_file).is_file():
        panel = io.read_panel(panel_file)
        if "cellpose" in panel and panel["cellpose"].notna().any():
            channel_groups = panel["cellpose"].values
    aggr_func = getattr(np, aggr_func_name)
    img_files = io.list_image_files(img_dir)
    Path(mask_dir).mkdir(exist_ok=True)

    if channels is not None:
        try:
            channel_list = list(map(int, channels.split(",")))
            if len(channel_list) != 2 or len(channel_list) != 1:
                raise ValueError(
                    "Invalid tuple format. Please provide two integers comma-separated as a string."
                )
            else:
                channels = channel_list
        except ValueError as e:
            raise click.BadParameter(str(e), param_hint="channels")
    else:
        channels = [1, 2]

    for img_file, mask, flow, style, diam in cellpose.try_segment_objects(
        img_files,
        pretrained_model,
        model_name,
        channelwise_minmax=channelwise_minmax,
        channelwise_zscore=channelwise_zscore,
        channel_groups=channel_groups,
        aggr_func=aggr_func,
        net_avg=net_avg,
        batch_size=batch_size,
        normalize=normalize,
        diameter=diameter,
        tile=tile,
        tile_overlap=tile_overlap,
        resample=resample,
        interp=interp,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        channels=channels,
        use_gpu=torch.cuda.is_available(),
    ):
        mask_file = io._as_path_with_suffix(Path(mask_dir) / img_file.name, ".tiff")
        io.write_mask(mask, mask_file)
        logger.info(mask_file)


@cellpose_cmd_group.command(
    name="train", help="Train a cellpose model using labeled data"
)
# model specification parameters
@click.option(
    "--model",
    "model_name",
    type=click.Choice(model_names),
    default="tissuenet",
    show_default=True,
    help="Name of the Cellpose model, choose on of the 14 pretrained models available in cellpose2",
)
@click.option(
    "--pretrained-model",
    "pretrained_model",
    type=click.Path(exists=True, dir_okay=False),
    help="Cellpose pretrained model to use as start for training",
)
@click.option(
    "--net-avg/--no-net-avg",
    "net_avg",
    default=True,
    show_default=True,
    help="load the 4 built-in networks and average them; load one network otherwise",
)
@click.option(
    "--diam-mean",
    "diam_mean",
    default=30.0,
    type=click.FLOAT,
    show_default=True,
    help="Mean diameter to resize cells to during training -- if starting from pretrained models it cannot be changed from 30.0",
)
@click.option(
    "--residual-on/--no-residual-on",
    "residual_on",
    default=True,
    show_default=True,
    help="Use 4 conv blocks with skip connections per layer instead of 2 conv blocks like conventional u-nets",
)
@click.option(
    "--style-on/--no-style-on",
    "style_on",
    default=True,
    show_default=True,
    help="Use skip connections from style vector to all upsampling layers",
)
@click.option(
    "--concatenation/--no-concatenation",
    "concatenation",
    default=False,
    show_default=True,
    help="Concatenate downsampling block outputs with upsampling block inputs; add otherwise",
)
@click.option(
    "--nchan",
    "nchan",
    default=2,
    type=click.INT,
    show_default=True,
    help="Number of channels to use as input to network, default is 2 (cyto + nuclei) or (nuclei + zeros)",
)
# #training parameters
@click.option(
    "--train-data",
    "train_data",
    default="cellpose_crops",
    show_default=True,
    type=click.Path(exists=True, file_okay=False),
    help="folder containing training data ",
)
@click.option(
    "--train-labels",
    "train_labels",
    default="cellpose_labels",
    show_default=True,
    type=click.Path(exists=True, file_okay=False),
    help="folder containing masks corresponding to images in training_data",
)
# this needs to be a list TODO
@click.option(
    "--train-files",
    "train_files",
    type=str,
    help="File names for images in train_data (to save flows for future runs), a list of strings",
)
# this needs to be a list TODO
@click.option(
    "--test-data",
    "test_data",
    help="images for testing, a list of arrays (2D or 3D)",
)
# this needs to be a list TODO
@click.option(
    "--test-labels",
    "test_labels",
    help="labels for test_data, where 0=no masks; 1,2,…=mask labels; can include flows as additional images, a list of arrays (2D or 3D)",
)
# this needs to be a list TODO
@click.option(
    "--test-files",
    "test_files",
    type=str,
    help="file names for images in test_data (to save flows for future runs), a list of strings",
)
@click.option(
    "--channels",
    "channels",
    type=str,
    help="channels to use for training. Please provide two comma-separated integers as a string",
)
@click.option(
    "--normalize/--no-normalize",
    "normalize",
    default=True,
    show_default=True,
    help="normalize data so 0.0=1st percentile and 1.0=99th percentile of image intensities in each channel",
)
@click.option(
    "--save-path",
    "save_path",
    show_default=True,
    type=click.Path(file_okay=False),
    help="where to save trained model, if None it is not saved",
)
@click.option(
    "--save-every",
    "save_every",
    default=50,
    show_default=True,
    type=click.INT,
    help="save network every [save_every] epochs",
)
@click.option(
    "--learning-rate",
    "learning_rate",
    default=0.1,
    show_default=True,
    type=click.FLOAT,
    help="Learning rate",
)
@click.option(
    "--n-epochs",
    "n_epochs",
    default=50,
    show_default=True,
    type=click.INT,
    help="how many times to go through whole training set during training",
)
@click.option(
    "--weight-decay",
    "weight_decay",
    default=0.0001,
    type=click.FLOAT,
    show_default=True,
    help="Weight decay",
)
@click.option(
    "--momentum",
    "momentum",
    default=0.9,
    type=click.FLOAT,
    show_default=True,
    help="not explaied in cellpose API documentation as of cellpose2.0",
)
@click.option(
    "--sgd/--no-sgd",
    "sgd",
    default=True,
    show_default=True,
    help="use SGD as optimization instead of RAdam",
)
@click.option(
    "--batch-size",
    "batch_size",
    default=8,
    type=click.INT,
    show_default=True,
    help="number of 224x224 patches to run simultaneously on the GPU (can make smaller or bigger depending on GPU memory usage).",
)
@click.option(
    "--nimg-per-epoch",
    "nimg_per_epoch",
    type=click.INT,
    help="minimum number of images to train on per epoch, with a small training set (< 8 images) it may help to set to 8. In not specified, all images in train-data re used for training per epoch",
)
@click.option(
    "--rescale/--no-rescale",
    "rescale",
    default=True,
    show_default=True,
    help="rescale images to diam_mean during training (assumes a size model will be fitted after training or the images will be resized accordingly); tries to train the model to be scale-invariant otherwise (works worse)",
)
@click.option(
    "--min-train-masks",
    "min_train_masks",
    default=5,
    type=click.INT,
    show_default=True,
    help="minimum number of masks an image must have to use in training set",
)
@click.option(
    "--model-name",
    "model_name",
    type=str,
    help="name of network, otherwise saved with name as params + training start time",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def train_cmd(
    pretrained_model,
    model_name,
    net_avg,
    diam_mean,
    residual_on,
    style_on,
    concatenation,
    nchan,
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
    sgd,
    batch_size,
    nimg_per_epoch,
    rescale,
    min_train_masks,
    model_type,
):
    if channels is not None:
        try:
            channel_list = list(map(int, channels.split(",")))
            if len(channel_list) != 2 or len(channel_list) != 1:
                raise ValueError(
                    "Invalid tuple format. Please provide two integers comma-separated as a string."
                )
            else:
                channels = channel_list
        except ValueError as e:
            raise click.BadParameter(str(e), param_hint="channels")
    else:
        channels = [1, 2]
    model_file = cellpose.try_train_model(
        gpu=torch.cuda.is_available(),
        model_type=model_type,
        pretrained_model=pretrained_model,
        net_avg=net_avg,
        diam_mean=diam_mean,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        residual_on=residual_on,
        style_on=style_on,
        concatenation=concatenation,
        nchan=nchan,
        # training parameters
        train_data=train_data,
        train_labels=train_labels,
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
        sgd=sgd,
        batch_size=batch_size,
        nimg_per_epoch=nimg_per_epoch,
        rescale=rescale,
        min_train_masks=min_train_masks,
        model_name=model_name,
    )
    logger.info(f"The trained model saved to: {model_file}")


@cellpose_cmd_group.command(
    name="prepare", help="Generate images and masks for training a cellpose model"
)
@click.option(
    "--pretrained-model",
    "pretrained_model",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to cellpose pretrained model to use as start for training",
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
    "--input-data",
    "input_data",
    default="img",
    show_default=True,
    type=click.Path(exists=True, file_okay=False),
    help="folder containing training data",
)
@click.option(
    "--cellpose-crops",
    "cellpose_crops",
    default="cellpose_crops",
    show_default=True,
    type=click.Path(file_okay=False),
    help="Destination for cellpose training crops",
)
@click.option(
    "--cellpose-labels",
    "cellpose_labels",
    default="cellpose_labels",
    show_default=True,
    type=click.Path(file_okay=False),
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
    "--model",
    "model_type",
    type=click.Choice(model_names),
    default="tissuenet",
    show_default=True,
    help="any model that is available in the GUI, use name in GUI e.g. ‘livecell’ (can be user-trained or model zoo)",
)
@click.option(
    "--pretrained-model",
    "pretrained_model",
    default=None,
    type=click.Path(exists=True, dir_okay=False),
    help="cellpose pretrained model to use as start for training",
)
@click.option(
    "--net-avg/--no-net-avg",
    "net_avg",
    default=True,
    show_default=True,
    help="load the 4 built-in networks and average them; load one network otherwise",
)
@click.option(
    "--diam-mean",
    "diam_mean",
    default=30.0,
    type=click.FLOAT,
    show_default=True,
    help="mean diameter to resize cells to during training -- if starting from pretrained models it cannot be changed from 30.0",
)
@click.option(
    "--residual-on/--no-residual-on",
    "residual_on",
    default=True,
    show_default=True,
    help="use 4 conv blocks with skip connections per layer instead of 2 conv blocks like conventional u-nets",
)
@click.option(
    "--style-on/--no-style-on",
    "style_on",
    default=True,
    show_default=True,
    help="use skip connections from style vector to all upsampling layers",
)
@click.option(
    "--concatenation/--no-concatenation",
    "concatenation",
    default=False,
    show_default=True,
    help="concatentate downsampling block outputs with upsampling block inputs; add otherwise",
)
@click.option(
    "--nchan",
    "nchan",
    default=2,
    type=click.INT,
    show_default=True,
    help="Number of channels to use as input to network, default is 2 (cyto + nuclei) or (nuclei + zeros)",
)
@click.option(
    "--batch-size",
    "batch_size",
    type=click.INT,
    default=8,
    show_default=True,
    help="number of 224x224 patches to run simultaneously on the GPU (can make smaller or bigger depending on GPU memory usage)",
)
@click.option(
    "--normalize/--no-normalize",
    "normalize",
    default=True,
    show_default=True,
    help="Normalize data so 0.0=1st percentile and 1.0=99th percentile of image intensities in each channel",
)
@click.option(
    "--diameter",
    "diameter",
    callback=float_or_none,
    default=30,
    show_default=True,
    help="if set to None, then diameter is automatically estimated if size model is loaded",
)
@click.option(
    "--tile/--no-tile",
    "tile",
    default=True,
    show_default=True,
    help="tiles image to ensure GPU/CPU memory usage limited (recommended)",
)
@click.option(
    "--tile-overlap",
    "tile_overlap",
    type=click.FLOAT,
    default=0.1,
    show_default=True,
    help="fraction of overlap of tiles when computing flows",
)
@click.option(
    "--resample/--no-resample",
    "resample",
    default=True,
    show_default=True,
    help="run dynamics at original image size (will be slower but create more accurate boundaries)",
)
@click.option(
    "--interp/--no-interp",
    "interp",
    default=True,
    show_default=True,
    help="interpolate during dynamics",
)
@click.option(
    "--flow-threshold",
    "flow_threshold",
    type=click.FLOAT,
    default=0.4,
    show_default=True,
    help="flow error threshold (all cells with errors below threshold are kept)",
)
@click.option(
    "--cellprob-threshold",
    "cellprob_threshold",
    type=click.FLOAT,
    default=-6,
    show_default=True,
    help="all pixels with value above threshold kept for masks, decrease to find more and larger masks",
)
@click.option(
    "--min-size",
    "min_size",
    type=click.INT,
    default=15,
    show_default=True,
    help="minimum number of pixels per mask, can turn off with -1",
)
@click.option(
    "--seed",
    "rand_seed",
    type=click.INT,
    default=123,
    help="Seed for random number generation",
)
@click.option(
    "--channels",
    "channels",
    type=str,
    help="Channels to use for training. Please provide two comma-separated integers as a string",
)
@click.option(
    "--save_crops/--no-save-crops",
    "save_crops",
    default=False,
    show_default=True,
    help="If True, the crops used for the initial segmentation are saved",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def train_prepare_cmd(
    input_data,
    cellpose_crops,
    cellpose_labels,
    panel_file,
    cellpose_crop_size,
    # model initiation
    pretrained_model,
    model_type,
    net_avg,
    diam_mean,
    residual_on,
    style_on,
    concatenation,
    nchan,
    # segmentation
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
    rand_seed,
    channels,
    save_crops,
):
    Path(cellpose_crops).mkdir(exist_ok=True)
    Path(cellpose_labels).mkdir(exist_ok=True)
    if channels is not None:
        try:
            channel_list = list(map(int, channels.split(",")))
            if len(channel_list) != 2:
                raise ValueError(
                    "Invalid tuple format. Please provide two integers comma-separated as a string."
                )
            else:
                channels = channel_list
        except ValueError as e:
            raise click.BadParameter(str(e), param_hint="channels")
    else:
        channels = [1, 2]
    if torch_available:
        gpu = torch.cuda.is_available()
        torch_device = torch.device("cuda" if gpu else "cpu")
    else:
        torch_device = None
        gpu = False

    for crop_file, label_file, masks in cellpose.prepare_training(
        input_data=input_data,
        cellpose_crops=cellpose_crops,
        cellpose_labels=cellpose_labels,
        panel_file=panel_file,
        cellpose_crop_size=cellpose_crop_size,
        # model parameters
        gpu=gpu,
        pretrained_model=pretrained_model,
        model_type=model_type,
        net_avg=net_avg,
        diam_mean=diam_mean,
        device=torch_device,
        residual_on=residual_on,
        style_on=style_on,
        concatenation=concatenation,
        nchan=nchan,
        # segmentation parameters
        batch_size=batch_size,
        channel_axis=0,
        channels=channels,
        normalize=normalize,
        diameter=diameter,
        tile=tile,
        tile_overlap=tile_overlap,
        resample=resample,
        interp=interp,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        rand_seed=rand_seed,
        save_crops=save_crops,
    ):
        io.write_mask(masks, label_file)
        logger.info("Crop image: %s", crop_file)
        logger.info("Crop label: %s", label_file)
