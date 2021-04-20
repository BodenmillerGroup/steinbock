import click
import sys

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from steinbock.preprocessing.imc import imc
from steinbock.utils import cli, io


def _extract_zips(path, suffix, dest):
    extracted_files = []
    for zip_file_path in Path(path).rglob("*.zip"):
        with ZipFile(zip_file_path) as zip_file:
            for zip_info in zip_file.infolist():
                zip_info_suffix = Path(zip_info.filename).suffix
                if not zip_info.is_dir() and zip_info_suffix == suffix:
                    extracted_file = zip_file.extract(zip_info, path=dest)
                    extracted_files.append(Path(extracted_file))
    return extracted_files


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
    "--unzip/--no-unzip",
    "unzip",
    default=True,
    show_default=True,
    help="Unzip .mcd/.txt files from .zip archives",
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
def imc_cmd(
    mcd_dir,
    txt_dir,
    panel_file,
    hpf,
    unzip,
    img_dir,
    dest_panel_file,
):
    with TemporaryDirectory() as temp_dir:
        mcd_files = imc.list_mcd_files(mcd_dir)
        if unzip:
            mcd_files += _extract_zips(mcd_dir, ".mcd", temp_dir)
        unique_mcd_file_stems = []
        for mcd_file in mcd_files:
            if mcd_file.stem in unique_mcd_file_stems:
                return click.echo(
                    f"Duplicated file stem: {mcd_file.stem}",
                    file=sys.stderr,
                )
            unique_mcd_file_stems.append(mcd_file.stem)
        txt_files = imc.list_txt_files(txt_dir)
        if unzip:
            txt_files += _extract_zips(txt_dir, ".txt", temp_dir)
        unique_txt_file_stems = []
        for txt_file in txt_files:
            if txt_file.stem in unique_txt_file_stems:
                return click.echo(
                    f"Duplicated file stem: {txt_file.stem}",
                    file=sys.stderr,
                )
            unique_txt_file_stems.append(txt_file.stem)
        dest_panel = imc.preprocess_panel(panel_file)
        dest_panel_file = io.write_panel(dest_panel, dest_panel_file)
        Path(img_dir).mkdir(exist_ok=True)
        for mcd_txt_file, acquisition_id, img in imc.preprocess_images(
            mcd_files,
            txt_files,
            dest_panel[imc.panel_metal_col].tolist(),
            hpf=hpf,
        ):
            img_file_stem = mcd_txt_file.stem
            if acquisition_id is not None:
                img_file_stem += f"_{acquisition_id}"
            img_file = io.write_image(img, Path(img_dir) / img_file_stem)
            click.echo(img_file)
            del img
