import click
import numpy as np

from pathlib import Path

from steinbock import io
from steinbock._env import check_steinbock_version, keras_models_dir
from steinbock.segmentation import deepcell

if deepcell.deepcell_available:
    import yaml
else:
    yaml = None

deepcell_cli_available = deepcell.deepcell_available

_model_paths = {}
if Path(keras_models_dir).is_dir():
    _model_paths.update({x.name: x for x in Path(keras_models_dir).iterdir()})

_applications = {
    "mesmer": deepcell.Application.MESMER,
}


@click.command(
    name="deepcell", help="Run a object segmentation batch using DeepCell"
)
@click.option(
    "--app",
    "application_name",
    type=click.Choice(list(_applications.keys()), case_sensitive=True),
    show_choices=True,
    default="mesmer",
    show_default=True,
    help="DeepCell application name",
)
@click.option(
    "--model",
    "model_path_or_name",
    type=click.STRING,
    default="MultiplexSegmentation",
    show_default=True,
    help=(
        "Path to custom Keras model or name of Keras model stored in "
        f"{keras_models_dir} [{', '.join(_model_paths.keys())}]"
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
    help="[Mesmer] Pixel size in micrometers",
)
@click.option(
    "--type",
    "segmentation_type",
    type=click.Choice(["whole-cell", "nuclear"]),
    default="whole-cell",
    show_default=True,
    show_choices=True,
    help="[Mesmer] Segmentation type",
)
@click.option(
    "--preprocess",
    "preprocess_file",
    type=click.Path(exists=True, dir_okay=False),
    help="[Mesmer] Preprocessing parameters (YAML file)",
)
@click.option(
    "--postprocess",
    "postprocess_file",
    type=click.Path(exists=True, dir_okay=False),
    help="[Mesmer] Postprocessing parameters (YAML file)",
)
@click.option(
    "-o",
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
    preprocess_file,
    postprocess_file,
    mask_dir,
):
    channel_groups = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if "deepcell" in panel and panel["deepcell"].notna().any():
            channel_groups = panel["deepcell"].values
    aggr_func = getattr(np, aggr_func_name)
    img_files = io.list_image_files(img_dir)
    model = None
    if model_path_or_name is not None:
        from tensorflow.keras.models import load_model

        if Path(model_path_or_name).exists():
            model = load_model(model_path_or_name, compile=False)
        elif model_path_or_name in _model_paths:
            model = load_model(_model_paths[model_path_or_name], compile=False)
    preprocess_kwargs = None
    if preprocess_file is not None:
        with Path(preprocess_file).open() as f:
            preprocess_kwargs = yaml.load(f)
    postprocess_kwargs = None
    if postprocess_file is not None:
        with Path(postprocess_file).open() as f:
            postprocess_kwargs = yaml.load(f)
    Path(mask_dir).mkdir(exist_ok=True)
    for img_file, mask in deepcell.try_segment_objects(
        img_files,
        _applications[application_name],
        model=model,
        channelwise_minmax=channelwise_minmax,
        channelwise_zscore=channelwise_zscore,
        channel_groups=channel_groups,
        aggr_func=aggr_func,
        pixel_size_um=pixel_size_um,
        segmentation_type=segmentation_type,
        preprocess_kwargs=preprocess_kwargs,
        postprocess_kwargs=postprocess_kwargs,
    ):
        mask_stem = Path(mask_dir) / img_file.stem
        mask_file = io.write_mask(mask, mask_stem)
        click.echo(mask_file)
