from pathlib import Path

import click
import click_log

from ... import io
from ..._cli.utils import catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from ..intensities import IntensityAggregation, try_measure_intensities_from_disk

_intensity_aggregations = {
    "sum": IntensityAggregation.SUM,
    "min": IntensityAggregation.MIN,
    "max": IntensityAggregation.MAX,
    "mean": IntensityAggregation.MEAN,
    "median": IntensityAggregation.MEDIAN,
    "std": IntensityAggregation.STD,
    "var": IntensityAggregation.VAR,
}


@click.command(name="intensities", help="Measure object intensities")
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--masks",
    "mask_dir",
    type=click.Path(exists=True, file_okay=False),
    default="masks",
    show_default=True,
    help="Path to the mask directory",
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
    "intensity_aggregation_name",
    type=click.Choice(list(_intensity_aggregations.keys()), case_sensitive=True),
    default="mean",
    show_default=True,
    help="Function for aggregating cell pixels",
)
@click.option(
    "--mmap/--no-mmap",
    "mmap",
    default=False,
    show_default=True,
    help="Use memory mapping for reading images/masks",
)
@click.option(
    "-o",
    "intensities_dir",
    type=click.Path(file_okay=False),
    default="intensities",
    show_default=True,
    help="Path to the object intensities output directory",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def intensities_cmd(
    img_dir,
    mask_dir,
    panel_file,
    intensity_aggregation_name,
    mmap,
    intensities_dir,
):
    panel = io.read_panel(panel_file)
    channel_names = panel["name"].tolist()
    img_files = io.list_image_files(img_dir)
    mask_files = io.list_mask_files(mask_dir, base_files=img_files)
    Path(intensities_dir).mkdir(exist_ok=True)
    for img_file, mask_file, intensities in try_measure_intensities_from_disk(
        img_files,
        mask_files,
        channel_names,
        _intensity_aggregations[intensity_aggregation_name],
        mmap=mmap,
    ):
        intensities_file = io._as_path_with_suffix(
            Path(intensities_dir) / img_file.name, ".csv"
        )
        io.write_data(intensities, intensities_file)
        logger.info(intensities_file)
        del intensities
