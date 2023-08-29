import logging
import os
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import Optional, Protocol, Union

import numpy as np
import pandas as pd
from skimage.io import imread, imsave
#from tifffile import imsave

from steinbock.classification.ilastik._ilastik import create_ilastik_crop

from ._segmentation import SteinbockSegmentationException

try:
    import cellpose.models

    cellpose_available = True
except Exception:
    cellpose_available = False

logger = logging.getLogger(__name__)
cellpose_available = find_spec("cellpose") is not None


class SteinbockTrainSegmentationException(SteinbockSegmentationException):
    pass


class AggregationFunction(Protocol):
    def __call__(self, img: np.ndarray, axis: Optional[int] = None) -> np.ndarray:
        ...


def try_train_model(

    gpu: bool,
    pretrained_model: str,
    model_type: str,
    net_avg: bool,
    diam_mean,
    device,
    residual_on:bool,
    style_on: bool,
    concatenation: bool,


    train_data: Union[str, PathLike],
    train_labels: Union[str, PathLike],
    train_files,
    test_data,
    test_labels,
    test_files,

    normalize: bool,
    save_path: str,
    save_every,
    learning_rate: float,
    n_epochs: int,
    weight_decay: float,
    momentum: float,
    SGD: bool,
    batch_size: int,
    nimg_per_epoch,
    rescale: bool,
    min_train_masks: int,
    model_name,
    channels: list = [1,2],

):
    rng = np.random.default_rng(123)
    # panel = pd.read_csv(panel_file, sep=',') #sorting the panel might be wise before or after loading
    model = cellpose.models.CellposeModel(
        gpu=gpu,
        model_type=pretrained_model,
        pretrained_model=pretrained_model,
        net_avg=net_avg,
        diam_mean = diam_mean,
        device=device,
        residual_on=residual_on,
        style_on=style_on,
        concatenation=concatenation,
        nchan=2
    )

    train_images = []
    count = 0
    for _, _, files in os.walk(train_data):
        files.sort()
        for f in files:
            if str(Path(f).stem).startswith(".") == False:
                dat = imread(Path(train_data, f))
                train_images.append(dat)
                count += 1
    print("Loaded", count, "images.")

    cp_dir = Path.home().joinpath(".cellpose")
    model_dir = cp_dir.joinpath("models")

    torch = True
    torch_str = ["", "torch"][torch]

    train_masks = []
    count = 0
    for _, _, files in os.walk(train_labels):
        files.sort()
        for f in files:
            if str(Path(f).stem).startswith(".") == False:
                dat = imread(Path(train_labels, f))
                train_masks.append(dat.astype(np.int16))
                count += 1
    print("Loaded", count, "masks.")

    old_pretrained_model = [
        os.fspath(model_dir.joinpath("%s%s_%d" % (pretrained_model, torch_str, j)))
        for j in range(4)
    ]
    model = cellpose.models.CellposeModel(
        model_type=pretrained_model, #diam_mean=diam_mean
    )
    myOutput = model.train(
        train_data=train_images,
        train_labels=train_masks,
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
        momentum=momentum,
        weight_decay=weight_decay,
        batch_size=batch_size,
        rescale=rescale,
    )
    return myOutput


def prepare_training(
    input_data: Union[str, PathLike],
    cellpose_crops: Union[str, PathLike],
    cellpose_masks: Union[str, PathLike],
    panel_file: str,
    cellpose_crop_size: int,

    gpu: bool,
    pretrained_model: Union[str, PathLike],
    model_type: str,
    diam_mean: float,
    device: bool,
    residual_on: bool,
    style_on: bool,
    concatenation: bool,

    normalize: bool,
    diameter: float,
    batch_size: int = 8,
    channels: list = [1, 2],
    channel_axis=0,
    net_avg: bool = True,
    tile: bool = False,
    tile_overlap: float = 0.1,
    resample: bool = True,
    interp: bool = True,
    flow_threshold: float = 1,
    cellprob_threshold: float = -6,
    min_size: int =15,
    progress=False,



):
    if not os.path.exists(cellpose_crops):
        os.makedirs(cellpose_crops)
    if not os.path.exists(cellpose_masks):
        os.makedirs(cellpose_masks)
    dir = os.listdir(input_data)
    rng = np.random.default_rng(123)
    panel = pd.read_csv(
        panel_file, sep=","
    )  # sorting the panel might be wise before or after loading
    model = cellpose.models.CellposeModel(
        gpu,
        pretrained_model,
        model_type,
        net_avg,
        diam_mean,
        device,
        residual_on,
        style_on,
        concatenation,
        nchan =2
    )

    for file in dir:
        f = os.path.join(input_data, file)
        if str(Path(f).stem).startswith(".") == False:
            test_img = imread(f)

            cellpose_crop_x, cellposek_crop_y, cellpose_crop = create_ilastik_crop(
                test_img, cellpose_crop_size, rng
            )
            print(cellpose_crop.shape)
            # cellpose_mask=cellpose_crop[0,:,:]
            # imsave("cellpose_crops/" + Path(f).stem + "_training_crop.tiff", cellpose_mask)
            Nuclear_img = np.sum(cellpose_crop[panel["cellpose"].values == 1], axis=0)
            Cytoplasmic_img = np.sum(
                cellpose_crop[panel["cellpose"].values == 2], axis=0
            )
            segstack = np.stack((Cytoplasmic_img, Nuclear_img), axis=0)
            #segstack = np.moveaxis(segstack, [0, 2], [2, 0])
            imsave(Path(cellpose_crops / Path(str(Path(f).stem) + ".tiff")), segstack)
            masks, flows, styles = model.eval(
                segstack,
                flow_threshold=1,
                cellprob_threshold=-6,

            )
            imsave(
                Path(cellpose_masks / Path(str(Path(f).stem) + "_masks.tiff")), masks
            )

    return cellpose_crops, cellpose_masks
