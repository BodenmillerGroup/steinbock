from pathlib import Path

import click
import click_log
import numpy as np

from ... import io
from ..._cli.utils import catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger


def _get_cellpose_module():
    try:
        from .. import cellpose as cellpose_module
    except ImportError as e:
        raise click.ClickException("The 'cellpose' command requires the optional Cellpose dependencies.") from e

    if not getattr(cellpose_module, "cellpose_available", False):
        raise click.ClickException(
            "The 'cellpose' command is not available because Cellpose dependencies "
            "are not installed in this environment."
        )

    return cellpose_module


try:
    from .. import cellpose as _cellpose_probe

    cellpose_cli_available = bool(getattr(_cellpose_probe, "cellpose_available", False))
except ImportError:
    cellpose_cli_available = False


@click.command(name="cellpose", help="Run an object segmentation batch using CellposeSAM")
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
    "--batch-size",
    "batch_size",
    type=click.INT,
    default=8,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--resample/--no-resample",
    "resample",
    default=False,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--channel-axis",
    "channel_axis",
    type=click.INT,
    default=0,
    show_default=True,
    help="See Cellpose documentation.",
)
@click.option(
    "--normalize/--no-normalize",
    "normalize",
    default=True,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--invert/--no-invert",
    "invert",
    default=False,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--rescale",
    "rescale",
    type=click.FLOAT,
    default=None,
    show_default=False,
    help="See Cellpose documentation",
)
@click.option(
    "--diameter",
    "diameter",
    type=click.FLOAT,
    default=None,
    show_default=False,
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
    "--cellprob-threshold",
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
@click.option(
    "--max-size-fraction",
    "max_size_fraction",
    type=click.FLOAT,
    default=0.4,
    show_default=True,
    help="See Cellpose documentation",
)
@click.option(
    "--niter",
    "niter",
    type=click.INT,
    default=None,
    help="See Cellpose documentation",
)
@click.option(
    "--augment/--no-augment",
    "augment",
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
    "-o",
    "mask_dir",
    type=click.Path(file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask output directory",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def cellpose_cmd(
    img_dir,
    channelwise_minmax,
    channelwise_zscore,
    panel_file,
    aggr_func_name,
    batch_size,
    resample,
    channel_axis,
    normalize,
    invert,
    rescale,
    diameter,
    flow_threshold,
    cellprob_threshold,
    min_size,
    max_size_fraction,
    niter,
    augment,
    tile_overlap,
    mask_dir,
):
    cellpose = _get_cellpose_module()

    channel_groups = None
    if Path(panel_file).is_file():
        panel = io.read_panel(panel_file)
        if "cellpose" in panel and panel["cellpose"].notna().any():
            channel_groups = panel["cellpose"].values

    try:
        aggr_func = getattr(np, aggr_func_name)
    except AttributeError as e:
        raise click.ClickException(f"Invalid numpy aggregation function: {aggr_func_name}") from e

    img_files = io.list_image_files(img_dir)
    Path(mask_dir).mkdir(exist_ok=True)

    for img_file, mask, _, _ in cellpose.try_segment_objects(
        img_files,
        channelwise_minmax=channelwise_minmax,
        channelwise_zscore=channelwise_zscore,
        channel_groups=channel_groups,
        aggr_func=aggr_func,
        batch_size=batch_size,
        resample=resample,
        channel_axis=channel_axis,
        normalize=normalize,
        invert=invert,
        rescale=rescale,
        diameter=diameter,
        flow_threshold=flow_threshold,
        cellprob_threshold=cellprob_threshold,
        min_size=min_size,
        max_size_fraction=max_size_fraction,
        niter=niter,
        augment=augment,
        tile_overlap=tile_overlap,
    ):
        mask_file = io._as_path_with_suffix(Path(mask_dir) / img_file.name, ".tiff")
        io.write_mask(mask, mask_file)
        logger.info(mask_file)
