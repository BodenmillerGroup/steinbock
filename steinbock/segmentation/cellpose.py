import logging
import os
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import Generator, Optional, Protocol, Sequence, Tuple, Union

import numpy as np
import pandas as pd
from skimage.io import imread
from tifffile import imsave

from steinbock.classification.ilastik._ilastik import create_ilastik_crop

from .. import io
from ._segmentation import SteinbockSegmentationException

try:
    import cellpose.models

    cellpose_available = True
except Exception:
    cellpose_available = False

logger = logging.getLogger(__name__)
cellpose_available = find_spec("cellpose") is not None


class SteinbockCellposeSegmentationException(SteinbockSegmentationException):
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
    residual_on: bool,
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
    channels: list = [1, 2],
):
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    rng = np.random.default_rng(123)
    # panel = pd.read_csv(panel_file, sep=',') #sorting the panel might be wise before or after loading
    model = cellpose.models.CellposeModel(
        gpu=gpu,
        model_type=pretrained_model,
        pretrained_model=pretrained_model,
        net_avg=net_avg,
        diam_mean=diam_mean,
        device=device,
        residual_on=residual_on,
        style_on=style_on,
        concatenation=concatenation,
        nchan=2,
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
        model_type=pretrained_model, diam_mean=diam_mean
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
    cellpose_labels: Union[str, PathLike],
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
    min_size: int = 15,
    progress=False,
):
    if not os.path.exists(cellpose_crops):
        os.makedirs(cellpose_crops)
    if not os.path.exists(cellpose_labels):
        os.makedirs(cellpose_labels)
    dir = os.listdir(input_data)
    rng = np.random.default_rng(123)
    panel = pd.read_csv(
        panel_file, sep=","
    )  # sorting the panel might be wise before or after loading
    if pretrained_model is not None:
        model_type = None
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
        nchan=2,
    )

    for file in dir:
        f = os.path.join(input_data, file)
        if str(Path(f).stem).startswith(".") == False:
            test_img = imread(f)

            cellpose_crop_x, cellposek_crop_y, cellpose_crop = create_ilastik_crop(
                test_img, cellpose_crop_size, rng
            )
            Nuclear_img = np.sum(cellpose_crop[panel["cellpose"].values == 1], axis=0)
            Cytoplasmic_img = np.sum(
                cellpose_crop[panel["cellpose"].values == 2], axis=0
            )
            segstack = np.stack((Cytoplasmic_img, Nuclear_img), axis=0)
            imsave(Path(cellpose_crops / Path(str(Path(f).stem) + ".tiff")), segstack)
            masks, flows, styles = model.eval(
                segstack,
                batch_size=batch_size,
                channels=channels,
                channel_axis=0,
                normalize=normalize,
                diameter=diameter,
                net_avg=net_avg,
                tile=tile,
                tile_overlap=tile_overlap,
                resample=resample,
                interp=interp,
                flow_threshold=flow_threshold,
                cellprob_threshold=cellprob_threshold,
                min_size=min_size,
                progress=False,
            )
            imsave(
                Path(cellpose_labels / Path(str(Path(f).stem) + "_masks.tiff")), masks
            )

    return cellpose_crops, cellpose_labels


def create_segmentation_stack(
    img: np.ndarray,
    channelwise_minmax: bool = False,
    channelwise_zscore: bool = False,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: AggregationFunction = np.mean,
) -> np.ndarray:
    if channelwise_minmax:
        channel_mins = np.nanmin(img, axis=(1, 2))
        channel_maxs = np.nanmax(img, axis=(1, 2))
        channel_ranges = channel_maxs - channel_mins
        img -= channel_mins[:, np.newaxis, np.newaxis]
        img[channel_ranges > 0] /= channel_ranges[
            channel_ranges > 0, np.newaxis, np.newaxis
        ]
    if channelwise_zscore:
        channel_means = np.nanmean(img, axis=(1, 2))
        channel_stds = np.nanstd(img, axis=(1, 2))
        img -= channel_means[:, np.newaxis, np.newaxis]
        img[channel_stds > 0] /= channel_stds[channel_stds > 0, np.newaxis, np.newaxis]
    if channel_groups is not None:
        img = np.stack(
            [
                aggr_func(img[channel_groups == channel_group], axis=0)
                for channel_group in np.unique(channel_groups)
                if not np.isnan(channel_group)
            ]
        )
    return img


def try_segment_objects(
    img_files: Sequence[Union[str, PathLike]],
    pretrained_model,
    model_name: str = "tissuenet",
    channelwise_minmax: bool = False,
    channelwise_zscore: bool = False,
    channel_groups: Optional[np.ndarray] = None,
    aggr_func: AggregationFunction = np.mean,
    net_avg: bool = True,
    batch_size: int = 8,
    normalize: bool = True,
    diameter: float = 10,
    tile: bool = False,
    tile_overlap: float = 0.1,
    resample: bool = True,
    interp: bool = True,
    flow_threshold: float = 1,
    cellprob_threshold: float = -6,
    min_size: int = 15,
    use_GPU: bool = False,
) -> Generator[Tuple[Path, np.ndarray, np.ndarray, np.ndarray, float], None, None]:
    # Here we need to seperate calls for sized ([nuclei, cyto and cyto2]) models and the non-sized ones ([tissuenet, livecell, CP, CPx, TN1, TN2, TN3, LC1, LC2, LC3, LC4] as of cellpose2.0)
    if model_name in ["nuclei", "cyto", "cyto2"] and pretrained_model is None:
        model = cellpose.models.Cellpose(
            gpu=use_GPU, model_type=model_name, net_avg=net_avg
        )
    else:
        model = cellpose.models.CellposeModel(
            model_type=model_name,
            pretrained_model=pretrained_model,
            net_avg=net_avg,
            diam_mean=diameter,
        )
    for img_file in img_files:
        try:
            img = create_segmentation_stack(
                io.read_image(img_file),
                channelwise_minmax=channelwise_minmax,
                channelwise_zscore=channelwise_zscore,
                channel_groups=channel_groups,
                aggr_func=aggr_func,
            )
            # channels: [cytoplasmic, nuclear]
            if img.shape[0] == 1:
                channels = [0, 0]  # grayscale image (cytoplasmic channel only)
            elif img.shape[0] == 2:
                channels = [2, 1]  # R=1 G=2 B=3 image (nuclear & cytoplasmic channels)
            else:
                raise SteinbockCellposeSegmentationException(
                    f"Invalid number of aggregated channels: "
                    f"expected 1 or 2, got {img.shape[0]}"
                )

            eval_results = model.eval(
                [img],
                batch_size=batch_size,
                channels=channels,
                channel_axis=0,
                normalize=normalize,
                diameter=diameter,
                net_avg=net_avg,
                tile=tile,
                tile_overlap=tile_overlap,
                resample=resample,
                interp=interp,
                flow_threshold=flow_threshold,
                cellprob_threshold=cellprob_threshold,
                min_size=min_size,
                progress=False,
            )
            masks, flows, styles = eval_results[:3]
            if len(eval_results) > 3:
                diams = eval_results[3]
                diam = diams if isinstance(diams, float) else diams[0]
            else:
                diam = None
            yield Path(img_file), masks[0], flows[0], styles[0], diam
            del img, masks, flows, styles

        except Exception as e:
            logger.exception(f"Error segmenting objects in {img_file}: {e}")
