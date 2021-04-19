import click

from pathlib import Path

from steinbock.tools.masks import masks
from steinbock.utils import cli, io


@click.group(
    name="masks",
    cls=cli.OrderedClickGroup,
    help="Process masks",
)
def masks_cmd():
    pass


@masks_cmd.command(
    help="Match objects from multiple masks",
)
@click.argument(
    "masks1",
    nargs=1,
    type=click.Path(exists=True, file_okay=False),
)
@click.argument(
    "masks2",
    nargs=1,
    type=click.Path(exists=True, file_okay=False),
)
@click.option(
    "-o",
    "table_dir",
    type=click.Path(file_okay=False),
    required=True,
    help="Path to the object table output directory",
)
def match(masks1, masks2, table_dir):
    if Path(masks1).is_file() and Path(masks2).is_file():
        mask_files1 = [Path(masks1)]
        mask_files2 = [Path(masks2)]
    else:
        mask_files1 = io.list_masks(masks1)
        mask_files2 = io.list_masks(masks2)
    table_dir = Path(table_dir)
    table_dir.mkdir(exist_ok=True)
    for mask_file1, mask_file2, table in masks.match(mask_files1, mask_files2):
        table_file = table_dir / mask_file1.name
        table.columns = [Path(masks1).name, Path(masks2).name]
        table.to_csv(table_file, index=False)
        click.echo(table_file)
        del table
