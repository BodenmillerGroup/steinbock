import logging
from importlib.util import find_spec
from os import PathLike
from pathlib import Path
from typing import Generator, Optional, Protocol, Sequence, Tuple, Union

import numpy as np

from .. import io
from ._segmentation import SteinbockSegmentationException

logger = logging.getLogger(__name__)
try:
    pass
except Exception as e:
    logger.exception(f"Could not import torch")

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


def create_cellpose_crop(
    cellpose_img: np.ndarray, cellpose_crop_size: int, rng: np.random.Generator
) -> Tuple[Optional[int], Optional[int], Optional[np.ndarray]]:
    if all(shape >= cellpose_crop_size for shape in cellpose_img.shape[1:]):
        cellpose_crop_x = 0
        if cellpose_img.shape[2] > cellpose_crop_size:
            cellpose_crop_x = rng.integers(cellpose_img.shape[2] - cellpose_crop_size)
        cellpose_crop_y = 0
        if cellpose_img.shape[1] > cellpose_crop_size:
            cellpose_crop_y = rng.integers(cellpose_img.shape[1] - cellpose_crop_size)
        cellpose_crop = cellpose_img[
            :,
            cellpose_crop_y : (cellpose_crop_y + cellpose_crop_size),
            cellpose_crop_x : (cellpose_crop_x + cellpose_crop_size),
        ]
        return (
            cellpose_crop_x,
            cellpose_crop_y,
            io._to_dtype(cellpose_crop, io.img_dtype),
        )
    return None, None, None


def try_train_model(
    gpu: bool,
    pretrained_model: str,
    model_type: str,
    net_avg: bool,
    diam_mean: float,
    # device: torch.device,
    device,
    residual_on: bool,
    style_on: bool,
    concatenation: bool,
    train_data: Union[str, PathLike],
    train_labels: Union[str, PathLike],
    train_files: Union[str, PathLike],
    test_data: Union[str, PathLike],
    test_labels: Union[str, PathLike],
    test_files: Union[str, PathLike],
    normalize: bool,
    save_path: str,
    save_every: int,
    learning_rate: float,
    n_epochs: int,
    weight_decay: float,
    momentum: float,
    sgd: bool,
    batch_size: int,
    nimg_per_epoch: int,
    rescale: bool,
    min_train_masks: int,
    model_name: str,
    channels: str = None,
):
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
    list_train_images = io.list_image_files(train_data)
    for file in list_train_images:
        dat = io.read_image(file)
        dat = dat.astype(int)
        train_images.append(dat)

    train_masks = []
    list_train_masks = io.list_mask_files(train_labels)
    for file in list_train_masks:
        dat = io.read_image(file)
        dat = dat.astype(int)
        train_masks.append(dat)

    model = cellpose.models.CellposeModel(
        model_type=pretrained_model, diam_mean=diam_mean
    )
    model_file = model.train(
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
        SGD=sgd,
        weight_decay=weight_decay,
        batch_size=batch_size,
        nimg_per_epoch=nimg_per_epoch,
        rescale=rescale,
        min_train_masks=min_train_masks,
        model_name=model_name,
    )
    return model_file


def prepare_training(
    input_data: Union[str, PathLike],
    cellpose_crops: Union[str, PathLike],
    cellpose_labels: Union[str, PathLike],
    pretrained_model: Union[str, PathLike],
    panel_file: str,
    cellpose_crop_size: int = 500,
    gpu: bool = False,
    model_type: str = "tissuenet",
    diam_mean: float = 30.0,
    device: bool = None,
    residual_on: bool = True,
    style_on: bool = True,
    concatenation: bool = False,
    normalize: bool = True,
    diameter: float = 10.0,
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
    seed: int = 123,
    progress=False,
) -> Generator[Tuple[str, str], None, None]:
    dir = io.list_image_files(input_data)
    rng = np.random.default_rng(seed)
    panel = io.read_panel(
        panel_file
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
        f = Path(file)
        test_img = io.read_image(f)

        cellpose_crop_x, cellposek_crop_y, cellpose_crop = create_cellpose_crop(
            test_img, cellpose_crop_size, rng
        )
        nuclear_img = np.sum(cellpose_crop[panel["cellpose"].values == 1], axis=0)
        cytoplasmic_img = np.sum(cellpose_crop[panel["cellpose"].values == 2], axis=0)
        segstack = np.stack((cytoplasmic_img, nuclear_img), axis=0)
        crop_file = Path(cellpose_crops) / (f.stem + ".tiff")
        io.write_image(segstack, crop_file)
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
        label_file = Path(cellpose_labels) / (f.stem + "_mask.tiff")
        io.write_mask(masks, label_file)
        yield tuple([str(crop_file), str(label_file)])


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
    pretrained_model: Union[str, PathLike],
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
    use_gpu: bool = False,
    channels: str = None,
) -> Generator[Tuple[Path, np.ndarray, np.ndarray, np.ndarray, float], None, None]:
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
            if img.shape[0] != 2:
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
