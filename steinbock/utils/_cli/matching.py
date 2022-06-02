from pathlib import Path

import click
import click_log

from ... import io
from ..._cli.utils import catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger
from .. import matching


@click.command(name="match", help="Match mask objects")
@click.argument("masks1", nargs=1, type=click.Path(exists=True, file_okay=False))
@click.argument("masks2", nargs=1, type=click.Path(exists=True, file_okay=False))
@click.option(
    "--mmap/--no-mmap",
    "mmap",
    default=False,
    show_default=True,
    help="Use memory mapping for reading images/masks",
)
@click.option(
    "-o",
    "csv_dir",
    type=click.Path(file_okay=False),
    required=True,
    help="Path to the object table CSV output directory",
)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def match_cmd(masks1, masks2, mmap, csv_dir):
    if Path(masks1).is_file() and Path(masks2).is_file():
        mask_files1 = [Path(masks1)]
        mask_files2 = [Path(masks2)]
    elif Path(masks1).is_dir() and Path(masks2).is_dir():
        mask_files1 = io.list_mask_files(masks1)
        mask_files2 = io.list_mask_files(masks2, base_files=mask_files1)
    Path(csv_dir).mkdir(exist_ok=True)
    for mask_file1, mask_file2, df in matching.try_match_masks_from_disk(
        mask_files1, mask_files2, mmap=mmap
    ):
        csv_file = io._as_path_with_suffix(Path(csv_dir) / mask_file1.name, ".csv")
        df.columns = [Path(masks1).name, Path(masks2).name]
        df.to_csv(csv_file, index=False)
        logger.info(csv_file)
        del df
