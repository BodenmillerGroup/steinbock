import click

from pathlib import Path
from xtiff import to_tiff

from steinbock import cli, io
from steinbock._env import check_version


@click.group(
    name="images",
    cls=cli.OrderedClickGroup,
    help="Image export",
)
def images_cmd_group():
    pass


@images_cmd_group.command(
    name="ometiff",
    help="Export images as OME-TIFF",
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default=cli.default_panel_file,
    show_default=True,
    help="Path to the panel file",
)
@click.option(
    "--dest",
    "ome_dir",
    type=click.Path(file_okay=False),
    default=cli.default_ome_dir,
    show_default=True,
    help="Path to the OME-TIFF export directory",
)
@check_version
def ometiff_cmd(img_dir, panel_file, ome_dir):
    panel = io.read_panel(panel_file)
    channel_names = panel[io.channel_name_col].tolist()
    ome_dir = Path(ome_dir)
    ome_dir.mkdir(exist_ok=True)
    for img_file in sorted(Path(img_dir).iterdir()):
        img = io.read_img(img_file)
        ome_file = ome_dir / img_file.with_suffix('.ome.tiff').name
        to_tiff(img, ome_file, channel_names=channel_names)
        click.echo(ome_file.name)
        del img
