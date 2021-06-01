import click
import numpy as np

from pathlib import Path
from tensorflow.keras.models import load_model

from steinbock import io
from steinbock._env import check_steinbock_version, keras_models_dir
from steinbock.segmentation import deepcell


_model_paths = {x.name: x for x in Path(keras_models_dir).iterdir()}


@click.command(
    name="deepcell", help="Run a object segmentation batch using DeepCell"
)
@click.option(
    "--app",
    "application_name",
    type=click.Choice(
        [deepcell.DeepcellApplication.MESMER.value], case_sensitive=True
    ),
    required=True,
    show_choices=True,
    help="DeepCell application name",
)
@click.option(
    "--model",
    "model_path_or_name",
    type=click.STRING,
    show_choices=True,
    help=(
        "Path to custom Keras model or name of Keras model stored in "
        f"{keras_models_dir} [{', '.join(_model_paths.keys())}]; "
        "do not specify to download default model for chosen application"
    ),
)
@click.option(
    "--img",
    "img_dir",
    type=click.Path(exists=True, file_okay=False),
    default="img",
    show_default=True,
    help="Path to the image directory",
)
@click.option(
    "--minmax/--no-minmax",
    "channelwise_minmax",
    default=False,
    show_default=True,
    help="Channel-wise min-max normalization",
)
@click.option(
    "--zscore/--no-zscore",
    "channelwise_zscore",
    default=False,
    show_default=True,
    help="Channel-wise z-score normalization",
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
    "aggr_func_name",
    type=click.STRING,
    default="mean",
    show_default=True,
    help="Numpy function for aggregating channel pixels",
)
@click.option(
    "--pixelsize",
    "pixel_size_um",
    type=click.FLOAT,
    default=1.0,
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
    default="masks",
    show_default=True,
    help="Path to the mask output directory",
)
@check_steinbock_version
def deepcell_cmd(
    application_name,
    model_path_or_name,
    img_dir,
    channelwise_minmax,
    channelwise_zscore,
    panel_file,
    aggr_func_name,
    pixel_size_um,
    segmentation_type,
    mask_dir,
):
    channel_groups = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if "deepcell" in panel:
            channel_groups = panel["deepcell"].values
    aggr_func = getattr(np, aggr_func_name)
    img_files = io.list_image_files(img_dir)
    application = deepcell.DeepcellApplication(application_name)
    model = None
    if model_path_or_name is not None:
        if Path(model_path_or_name).exists():
            model = load_model(model_path_or_name)
        else:
            model = load_model(_model_paths[model_path_or_name])
    Path(mask_dir).mkdir(exist_ok=True)
    for img_file, mask in deepcell.run_object_segmentation(
        img_files,
        application,
        model=model,
        channelwise_minmax=channelwise_minmax,
        channelwise_zscore=channelwise_zscore,
        channel_groups=channel_groups,
        aggr_func=aggr_func,
        pixel_size_um=pixel_size_um,
        segmentation_type=segmentation_type,
    ):
        mask_stem = Path(mask_dir) / img_file.stem
        mask_file = io.write_mask(mask, mask_stem)
        click.echo(mask_file)
