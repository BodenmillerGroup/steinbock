import click

from pathlib import Path

from steinbock.preprocessing.imc.imc import preprocess_images
from steinbock.utils import cli, io

_keep_panel_col = "keep"


@click.command(
    help="Extract images from Imaging Mass Cytometry (IMC) .mcd/.txt files",
)
@click.option(
    "--mcd",
    "mcd_dir",
    type=click.Path(exists=True, file_okay=False),
    default="raw",
    show_default=True,
    help="Path to the .mcd file directory",
)
@click.option(
    "--txt",
    "txt_dir",
    type=click.Path(exists=True, file_okay=False),
    default="raw",
    show_default=True,
    help="Path to the .txt file directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default=cli.default_panel_file,
    show_default=True,
    help="Path to the panel .csv file",
)
@click.option(
    "--dest",
    "img_dir",
    type=click.Path(file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image output directory",
)
@click.option(
    "--hpf",
    "hpf",
    type=click.FLOAT,
    help="Hot pixel filter (specify delta threshold)",
)
def imc(mcd_dir, txt_dir, panel_file, img_dir, hpf):
    mcd_files = sorted(Path(mcd_dir).rglob("*.mcd"))
    txt_files = sorted(Path(txt_dir).rglob("*.txt"))
    channel_indices = None
    if Path(panel_file).exists():
        channel_indices = io.read_panel(panel_file).index.values
    Path(img_dir).mkdir(exist_ok=True)
    for mcd_txt_file, acquisition_id, img in preprocess_images(
        mcd_files,
        txt_files,
        img_dir,
        channel_indices=channel_indices,
        hpf=hpf,
    ):
        if acquisition_id is not None:
            img_file_name = f"{mcd_txt_file.stem}_{acquisition_id}.tiff"
        else:
            img_file_name = f"{mcd_txt_file.stem}.tiff"
        img_file = Path(img_dir) / img_file_name
        io.write_image(img, img_file)
        click.echo(mcd_txt_file.name)
