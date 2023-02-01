from pathlib import Path

import click
import click_log

from ... import io
from ..._cli.utils import catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import expansion


@click.command(name="expand", help="Expand mask objects by an Euclidean distance")
@click.argument("masks", type=click.Path(exists=True, file_okay=False))
@click.argument("distance", type=click.INT)
@click.option(
    "--mmap/--no-mmap",
    "mmap",
    default=False,
    show_default=True,
    help="Use memory mapping for reading images/masks",
)
@click.option(
    "-o",
    "expanded_masks_dir",
    type=click.Path(file_okay=False),
    help="Path to the expanded masks output directory",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def expand_cmd(masks, distance, mmap, expanded_masks_dir):
    if Path(masks).is_file():
        mask_files = [Path(masks)]
    elif Path(masks).is_dir():
        mask_files = io.list_mask_files(masks)
    if expanded_masks_dir is not None:
        Path(expanded_masks_dir).mkdir(exist_ok=True)
    else:
        expanded_masks_dir = Path(masks)
    for mask_file, expanded_mask in expansion.try_expand_masks_from_disk(
        mask_files, distance, mmap=mmap
    ):
        expanded_mask_file = Path(expanded_masks_dir) / mask_file.name
        io.write_mask(expanded_mask, expanded_mask_file, ignore_dtype=True)
        logger.info(expanded_mask_file)
        del expanded_mask
