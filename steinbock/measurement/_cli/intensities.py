import click

from pathlib import Path

from steinbock import io
from steinbock._env import check_steinbock_version
from steinbock.measurement import data


_measurements = {
    "sum": data.Measurement.SUM,
    "min": data.Measurement.MIN,
    "max": data.Measurement.MAX,
    "mean": data.Measurement.MEAN,
    "median": data.Measurement.MEDIAN,
    "std": data.Measurement.STD,
    "var": data.Measurement.VAR,
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
    "--mask",
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
    "measurement_name",
    type=click.Choice(list(_measurements.keys()), case_sensitive=True),
    default="mean",
    show_default=True,
    help="Function for aggregating cell pixels",
)
@click.option(
    "--dest",
    "intensities_dir",
    type=click.Path(file_okay=False),
    default="intensities",
    show_default=True,
    help="Path to the object intensities output directory",
)
@check_steinbock_version
def intensities_cmd(
    img_dir, mask_dir, panel_file, measurement_name, intensities_dir
):
    panel = io.read_panel(panel_file)
    channel_names = panel["name"].tolist()
    img_files = io.list_image_files(img_dir)
    mask_files = io.list_mask_files(mask_dir, base_files=img_files)
    Path(intensities_dir).mkdir(exist_ok=True)
    for img_file, mask_file, intensities in data.measure_intensities_from_disk(
        img_files, mask_files, channel_names, _measurements[measurement_name],
    ):
        intensities_stem = Path(intensities_dir) / img_file.stem
        intensities_file = io.write_data(
            intensities, intensities_stem, copy=False
        )
        click.echo(intensities_file)
        del intensities
