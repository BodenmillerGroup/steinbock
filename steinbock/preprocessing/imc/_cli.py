import click
import sys

from pathlib import Path

from steinbock.preprocessing.imc import imc
from steinbock.utils import cli, io


@click.command(
    name="imc",
    help="Extract Imaging Mass Cytometry (IMC) images",
)
@click.option(
    "--mcd",
    "mcd_dir",
    type=click.Path(exists=True, file_okay=False),
    default="raw",
    show_default=True,
    help="Path to the IMC .mcd file directory",
)
@click.option(
    "--txt",
    "txt_dir",
    type=click.Path(exists=True, file_okay=False),
    default="raw",
    show_default=True,
    help="Path to the IMC .txt file directory",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(exists=True, dir_okay=False),
    default=str(Path("raw", "panel.csv")),
    show_default=True,
    help="Path to the IMC panel file",
)
@click.option(
    "--hpf",
    "hpf",
    type=click.FLOAT,
    help="Hot pixel filter (specify delta threshold)",
)
@click.option(
    "--imgdest",
    "img_dir",
    type=click.Path(file_okay=False),
    default=cli.default_img_dir,
    show_default=True,
    help="Path to the image output directory",
)
@click.option(
    "--paneldest",
    "dest_panel_file",
    type=click.Path(dir_okay=False),
    default=cli.default_panel_file,
    show_default=True,
    help="Path to the panel output file",
)
def imc_cmd(mcd_dir, txt_dir, panel_file, hpf, img_dir, dest_panel_file):
    mcd_files = imc.list_mcd_files(mcd_dir)
    unique_mcd_file_names = []
    for mcd_file in mcd_files:
        if mcd_file.name in unique_mcd_file_names:
            return click.echo(
                f"Duplicated file name: {mcd_file.name}",
                file=sys.stderr,
            )
        unique_mcd_file_names.append(mcd_file.name)
    txt_files = imc.list_txt_files(txt_dir)
    unique_txt_file_names = []
    for txt_file in txt_files:
        if txt_file.name in unique_txt_file_names:
            return click.echo(
                f"Duplicated file name: {mcd_file.name}",
                file=sys.stderr,
            )
        unique_txt_file_names.append(txt_file.name)
    dest_panel, metal_order = imc.preprocess_panel(panel_file)
    dest_panel_file = io.write_panel(dest_panel, dest_panel_file)
    Path(img_dir).mkdir(exist_ok=True)
    for mcd_txt_file, acquisition_id, img in imc.preprocess_images(
        mcd_files,
        txt_files,
        metal_order,
        hpf=hpf,
    ):
        img_file_name = mcd_txt_file.stem
        if acquisition_id is not None:
            img_file_name += f"_{acquisition_id}"
        img_file = io.write_image(img, Path(img_dir) / img_file_name)
        click.echo(img_file)
