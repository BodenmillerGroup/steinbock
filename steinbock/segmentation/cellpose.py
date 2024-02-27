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
    import torch

    torch_available = True
except Exception as e:
    torch_available = False

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
    def __call__(self, img: np.ndarray, axis: Optional[int] = None) -> np.ndarray: ...


def create_cellpose_crop(
    cellpose_img: np.ndarray, cellpose_crop_size: int, rng: np.random.Generator
) -> Tuple[Optional[int], Optional[int], Optional[np.ndarray]]:
    if all(shape >= cellpose_crop_size for shape in cellpose_img.shape[1:]):
        cellpose_crop_x = 0
        cellpose_crop_x = rng.integers(cellpose_img.shape[2] - cellpose_crop_size)
        cellpose_crop_y = 0
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
    device: "Union[torch.device, None]",
    residual_on: bool,
    style_on: bool,
    concatenation: bool,
    nchan: int,
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
    channels: list,
):
    model = cellpose.models.CellposeModel(
        gpu=gpu,
        model_type=model_type,
        pretrained_model=pretrained_model,
        net_avg=net_avg,
        diam_mean=diam_mean,
        device=device,
        residual_on=residual_on,
        style_on=style_on,
        concatenation=concatenation,
        nchan=nchan,
    )
    train_images = []
    list_train_images = io.list_image_files(train_data)
    for file in list_train_images:
        dat = io.read_image(file)
        # dat = io. _to_dtype(dat, np.dtype(int))
        train_images.append(dat)

    train_masks = []
    list_train_masks = io.list_mask_files(train_labels, base_files=list_train_images)
    for file in list_train_masks:
        dat = io.read_image(file)
        dat = io._to_dtype(dat, np.dtype(int))
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
    cellpose_crop_size: int,
    gpu: bool,
    model_type: str,
    diam_mean: float,
    device: bool,
    residual_on: bool,
    style_on: bool,
    concatenation: bool,
    nchan: bool,
    normalize: bool,
    diameter: Union[None, float],
    batch_size: int,
    channels: str,
    channel_axis: int,
    net_avg: bool,
    tile: bool,
    tile_overlap: float,
    resample: bool,
    interp: bool,
    flow_threshold: float,
    cellprob_threshold: float,
    min_size: int,
    rand_seed: int,
    save_crops: bool,
    progress: bool = False,
) -> Generator[Tuple[str, str], None, None]:
    inpt_dir = io.list_image_files(input_data)
    rng = np.random.default_rng(rand_seed)
    panel = io.read_panel(panel_file)
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
        nchan,
    )

    for file in inpt_dir:
        f = Path(file)
        test_img = io.read_image(f)

        cellpose_crop_x, cellposek_crop_y, cellpose_crop = create_cellpose_crop(
            test_img, cellpose_crop_size, rng
        )
        nuclear_img = np.sum(cellpose_crop[panel["cellpose"].values == 1], axis=0)
        cytoplasmic_img = np.sum(cellpose_crop[panel["cellpose"].values == 2], axis=0)
        segstack = np.stack((cytoplasmic_img, nuclear_img), axis=0)
        crop_file = Path(cellpose_crops) / (f.stem + ".tiff")
        if save_crops:
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
        label_file = Path(cellpose_labels) / (f.stem + ".tiff")
        yield str(crop_file), str(label_file), masks


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
    model_type: str,
    channelwise_minmax: bool,
    channelwise_zscore: bool,
    channel_groups: Optional[np.ndarray],
    aggr_func: AggregationFunction,
    net_avg: bool,
    batch_size: int,
    normalize: bool,
    diameter: Union[None, float],
    tile: bool,
    tile_overlap: float,
    resample: bool,
    interp: bool,
    flow_threshold: float,
    cellprob_threshold: float,
    min_size: int,
    use_gpu: bool,
    channels: str,
) -> Generator[Tuple[Path, np.ndarray, np.ndarray, np.ndarray, float], None, None]:

    model = cellpose.models.CellposeModel(
        model_type=model_type,
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
