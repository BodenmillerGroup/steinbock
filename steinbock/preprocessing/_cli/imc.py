import click
import pandas as pd
import sys

from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from steinbock import io
from steinbock._cli.utils import OrderedClickGroup
from steinbock._env import check_steinbock_version
from steinbock.preprocessing import imc


imc_cli_available = imc.imc_available


@click.group(
    name="imc",
    cls=OrderedClickGroup,
    help="Preprocess Imaging Mass Cytometry (IMC) data",
)
def imc_cmd_group():
    pass


@imc_cmd_group.command(
    name="panel", help="Create a panel from IMC panel/image data"
)
@click.option(
    "--imcpanel",
    "imc_panel_file",
    type=click.Path(dir_okay=False),
    default=str(Path("raw", "panel.csv")),
    show_default=True,
    help="Path to the IMC panel file",
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
    "-o",
    "panel_file",
    type=click.Path(dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the panel output file",
)
@check_steinbock_version
def panel_cmd(imc_panel_file, mcd_dir, txt_dir, panel_file):
    panel = None
    if Path(imc_panel_file).exists():
        panel = imc.create_panel_from_imc_panel(imc_panel_file)
    if panel is None:
        mcd_files = _collect_mcd_files(mcd_dir)
        if len(mcd_files) > 0:
            panel = imc.create_panel_from_mcd_files(mcd_files)
    if panel is None:
        txt_files = _collect_txt_files(txt_dir)
        if len(txt_files) > 0:
            panel = imc.create_panel_from_txt_files(txt_files)
    if panel is None:
        return click.echo(
            "ERROR: No panel/.mcd/.txt file found", file=sys.stderr
        )
    io.write_panel(panel, panel_file)


@imc_cmd_group.command(
    name="images", help="Extract Imaging Mass Cytometry (IMC) images"
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
    "--unzip/--no-unzip",
    "unzip",
    default=True,
    show_default=True,
    help="Unzip .mcd/.txt files from .zip archives",
)
@click.option(
    "--panel",
    "panel_file",
    type=click.Path(dir_okay=False),
    default="panel.csv",
    show_default=True,
    help="Path to the steinbock panel file",
)
@click.option(
    "--hpf",
    "hpf",
    type=click.FLOAT,
    help="Hot pixel filter (specify delta threshold)",
)
@click.option(
    "--imgout",
    "img_dir",
    type=click.Path(file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image output directory",
)
@click.option(
    "--infoout",
    "image_info_file",
    type=click.Path(dir_okay=False),
    default="images.csv",
    show_default=True,
    help="Path to the image information output file",
)
@check_steinbock_version
def images_cmd(
    mcd_dir, txt_dir, unzip, panel_file, hpf, img_dir, image_info_file
):
    channel_names = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if "channel" in panel:
            channel_names = panel["channel"].tolist()
    image_info_data = []
    with (TemporaryDirectory() if unzip else nullcontext()) as temp_dir:
        mcd_files = _collect_mcd_files(mcd_dir, unzip_dir=temp_dir)
        txt_files = _collect_txt_files(txt_dir, unzip_dir=temp_dir)
        Path(img_dir).mkdir(exist_ok=True)
        mcd_txt_files = {}
        num_dupl = 0
        for (
            mcd_txt_file,
            acquisition,
            img,
            recovery_file,
            recovered,
        ) in imc.try_preprocess_images_from_disk(
            mcd_files, txt_files, channel_names=channel_names, hpf=hpf
        ):
            img_file_stem = Path(mcd_txt_file).stem
            if acquisition is not None:
                img_file_stem += f"_{acquisition.id:03d}"
            if img_file_stem in mcd_txt_files:
                num_dupl += 1
                first_mcd_txt_file = mcd_txt_files[img_file_stem][0]
                img_file_stem = f"DUPLICATE{num_dupl:03d}_" + img_file_stem
                click.echo(
                    f"WARNING: File {mcd_txt_file} is a duplicate of "
                    f"{first_mcd_txt_file}, saving as {img_file_stem}",
                    file=sys.stderr,
                )
                mcd_txt_files[img_file_stem].append(mcd_txt_file)
            else:
                mcd_txt_files[img_file_stem] = [mcd_txt_file]
            img_file = io.write_image(img, Path(img_dir) / img_file_stem)
            recovery_file_name = None
            if recovery_file is not None:
                recovery_file_name = recovery_file.name
            image_info_row = {
                "image": img_file.name,
                "width_px": img.shape[2],
                "height_px": img.shape[1],
                "num_channels": img.shape[0],
                "source_file": mcd_txt_file.name,
                "recovery_file": recovery_file_name,
                "recovered": recovered,
            }
            if acquisition is not None:
                image_info_row.update(
                    {
                        "acquisition_id": acquisition.id,
                        "acquisition_description": acquisition.description,
                        "acquisition_start_x_um": (
                            acquisition.roi_points_um[0][0]
                        ),
                        "acquisition_start_y_um": (
                            acquisition.roi_points_um[0][1]
                        ),
                        "acquisition_end_x_um": (
                            acquisition.roi_points_um[2][0]
                        ),
                        "acquisition_end_y_um": (
                            acquisition.roi_points_um[2][1]
                        ),
                        "acquisition_width_um": acquisition.width_um,
                        "acquisition_height_um": acquisition.height_um,
                    }
                )
            image_info_data.append(image_info_row)
            click.echo(img_file)
            del img
    image_info = pd.DataFrame(data=image_info_data)
    io.write_image_info(image_info, image_info_file)


def _extract_zips(path, suffix, dest):
    extracted_files = []
    for zip_file_path in Path(path).rglob("*.zip"):
        with ZipFile(zip_file_path) as zip_file:
            zip_infos = sorted(zip_file.infolist(), key=lambda x: x.filename)
            for zip_info in zip_infos:
                zip_info_suffix = Path(zip_info.filename).suffix
                if not zip_info.is_dir() and zip_info_suffix == suffix:
                    extracted_file = zip_file.extract(zip_info, path=dest)
                    extracted_files.append(Path(extracted_file))
    return extracted_files


def _collect_mcd_files(mcd_dir, unzip_dir=None):
    mcd_files = imc.list_mcd_files(mcd_dir)
    if unzip_dir is not None:
        mcd_files += _extract_zips(mcd_dir, ".mcd", unzip_dir)
    # unique_mcd_stem_names = []
    # for mcd_file in mcd_files:
    #     if mcd_file.stem in unique_mcd_stem_names:
    #         return click.echo(
    #             f"ERROR: Duplicated file stem {mcd_file.stem}",
    #             file=sys.stderr
    #         )
    #     unique_mcd_stem_names.append(mcd_file.stem)
    return mcd_files


def _collect_txt_files(txt_dir, unzip_dir=None):
    txt_files = imc.list_txt_files(txt_dir)
    if unzip_dir is not None:
        txt_files += _extract_zips(txt_dir, ".txt", unzip_dir)
    # unique_txt_stem_names = []
    # for txt_file in txt_files:
    #     if txt_file.stem in unique_txt_stem_names:
    #         return click.echo(
    #             f"ERROR: Duplicated file stem {txt_file.stem}",
    #             file=sys.stderr
    #         )
    #     unique_txt_stem_names.append(txt_file.stem)
    return txt_files
