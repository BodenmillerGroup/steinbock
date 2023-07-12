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
@click.option(
    "--cropsize",
    "cellpose_crop_size",
    type=click.INT,
    default=512,
    show_default=True,
    help="Cellpose crop size (in pixels)",
)
@click.option(
    "--pretrained_model",
    "pretrained_model",
    default="TN2",
    show_default=True,
    help="cellpose pretrained model to use as start for training",
)
@click.option(
    "--diam_mean",
    "diam_mean",
    default=30.0,
    type=float,
    help="mean diameter to resize cells to during training -- if starting from pretrained models it cannot be changed from 30.0",
)
@click.option(
    "--train_data",
    "train_data",
    default=[],
    type=str,
    required=True,
    help="folder containing training data ",
)
@click.option(
    "--train_mask",
    "train_mask",
    default="train_masks",
    type=str,
    help="folder containing masks corresponding to images in training_data",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def train_run_cmd(
    pretrained_model,
    diam_mean,
    train_data,
    train_mask,
    cellpose_crop_size,
):
    # os.mkdir("cellpose_crops")
    Path("cellpose_crops").mkdir(exist_ok=True)
    Path("masks").mkdir(exist_ok=True)
    Path("training_out").mkdir(exist_ok=True)

    model_file = train.try_train_model(pretrained_model, train_data, train_mask)
    print(f"The trained model file can be found here: {model_file}")
    logger.info(model_file)


@train_cmd_group.command(
    name="prepare", help="Generate images and masks for training a cellpose model"
)
@click.option(
    "--pretrained_model",
    "pretrained_model",
    default="TN2",
    show_default=True,
    help="cellpose pretrained model to use as start for training",
)
@click.option(
    "--cropsize",
    "cellpose_crop_size",
    type=click.INT,
    default=512,
    show_default=True,
    help="Cellpose crop size (in pixels)",
)
@click.option(
    "--diam_mean",
    "diam_mean",
    default=30.0,
    type=float,
    help="mean diameter to resize cells to during training -- if starting from pretrained models it cannot be changed from 30.0",
)
@click.option(
    "--input_data",
    "input_data",
    default=[],
    type=str,
    required=True,
    help="folder containing training data ",
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
    "--train_mask",
    "train_mask",
    default="train_masks",
    type=str,
    help="folder containing masks corresponding to images in training_data",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def train_prepare_cmd(
    panel_file,
    pretrained_model,
    diam_mean,
    input_data,
    train_mask,
    cellpose_crop_size,
):
    # os.mkdir("cellpose_crops")
    Path("cellpose_crops").mkdir(exist_ok=True)
    Path("masks").mkdir(exist_ok=True)
    Path("training_out").mkdir(exist_ok=True)

    crop_loc, mask_loc = train.prepare_training(
        pretrained_model, input_data, train_mask, panel_file=panel_file
    )
    print(f"Cellpose traing crops in: {crop_loc}")
    print(f"Cellpose traing masks in {mask_loc}")
    # logger.info(model_file)
