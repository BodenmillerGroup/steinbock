import click
import numpy as np

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version, keras_models_dir
from steinbock.segmentation.deepcell import deepcell


_models = {x.name: x for x in Path(keras_models_dir).iterdir()}


@click.command(
    name="deepcell",
    help="Run a object segmentation batch using DeepCell",
)
@click.option(
    "--app",
    "application_name",
    type=click.Choice(
        [deepcell.Application.MESMER.value],
        case_sensitive=False,
    ),
    required=True,
    show_choices=True,
    help="DeepCell application name",
)
@click.option(
    "--model",
    "model_name",
    type=click.Choice(
        list(_models.keys()),
        case_sensitive=True,
    ),
    show_choices=True,
    help=(
        "Name of the saved Keras model "
        "(do not specify to download default model)"
    ),
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
    "--aggr",
    "aggr_func_name",
    type=click.STRING,
    default="mean",
    show_default=True,
    help="Numpy function for aggregating channel pixels",
)
@click.option(
    "--minmax/--no-minmax",
    "minmax",
    default=False,
    show_default=True,
    help="Channel-wise min-max normalization",
)
@click.option(
    "--zscore/--no-zscore",
    "zscore",
    default=False,
    show_default=True,
    help="Channel-wise z-score normalization",
)
@click.option(
    "--pixelsize",
    "pixel_size_um",
    type=click.FLOAT,
    default=1.,
    show_default=True,
    help="Pixel size in micrometers (Mesmer only)",
)
@click.option(
    "--type",
    "segmentation_type",
    type=click.Choice(["whole-cell", "nuclear"]),
    default="whole-cell",
    show_default=True,
    show_choices=True,
    help="Segmentation type (Mesmer only)",
)
@click.option(
    "--dest",
    "mask_dir",
    type=click.Path(file_okay=False),
    default=cli.default_mask_dir,
    show_default=True,
    help="Path to the mask output directory",
)
@check_version
def deepcell_cmd(
    application_name,
    model_name,
    img_dir,
    panel_file,
    aggr_func_name,
    minmax,
    zscore,
    pixel_size_um,
    segmentation_type,
    mask_dir,
):
    channel_groups = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if deepcell.panel_deepcell_col in panel:
            channel_groups = panel[deepcell.panel_deepcell_col].values
    aggr_func = getattr(np, aggr_func_name)
    application = deepcell.Application(application_name)
    model = None
    if model_name is not None:
        from tensorflow.keras.models import load_model
        model = load_model(_models[model_name])
    Path(mask_dir).mkdir(exist_ok=True)
    for img_file, mask in deepcell.run_object_segmentation(
        img_dir,
        application,
        model=model,
        channelwise_minmax=minmax,
        channelwise_zscore=zscore,
        channel_groups=channel_groups,
        aggr_func=aggr_func,
        pixel_size_um=pixel_size_um,
        segmentation_type=segmentation_type,
    ):
        mask_file = io.write_mask(mask, Path(mask_dir) / img_file.stem)
        click.echo(mask_file)
