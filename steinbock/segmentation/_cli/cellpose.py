from pathlib import Path

import click
import click_log
import numpy as np

from ... import io
from ..._cli.utils import catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import cellpose

cellpose_cli_available = cellpose.cellpose_available


@click.command(name="cellpose", help="Run an object segmentation batch using Cellpose")
@click.option(
    "--model",
    "model_name",
    type=click.Choice(["nuclei", "cyto", "cyto2"]),
    default="cyto2",
    show_default=True,
    help="Name of the Cellpose model",
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
    help="See Cellpose documentation",
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
    "--cellprobab-threshold",
    "cellprobab_threshold",
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
    cellprobab_threshold,
    min_size,
    mask_dir,
):
    channel_groups = None
    if Path(panel_file).is_file():
        panel = io.read_panel(panel_file)
        if "cellpose" in panel and panel["cellpose"].notna().any():
            channel_groups = panel["cellpose"].values
    aggr_func = getattr(np, aggr_func_name)
    img_files = io.list_image_files(img_dir)
    Path(mask_dir).mkdir(exist_ok=True)
    for img_file, mask, flow, style, diam in cellpose.try_segment_objects(
        model_name,
        img_files,
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
        cellprob_threshold=cellprobab_threshold,
        min_size=min_size,
    ):
        mask_file = io._as_path_with_suffix(Path(mask_dir) / img_file.name, ".tiff")
        io.write_mask(mask, mask_file)
        logger.info(mask_file)
