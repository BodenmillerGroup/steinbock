from pathlib import Path

import click
import click_log
import numpy as np

from ... import io
from ..._cli.utils import catch_exception, logger
from ..._steinbock import SteinbockException
from ..._steinbock import logger as steinbock_logger


def _get_deepcell_module():
    try:
        from .. import deepcell as deepcell_module
    except ImportError as e:
        raise click.ClickException("The 'deepcell' command requires the optional DeepCell dependencies.") from e

    if not getattr(deepcell_module, "deepcell_available", False):
        raise click.ClickException(
            "The 'deepcell' command is not available because DeepCell dependencies "
            "are not installed in this environment."
        )

    return deepcell_module


def _get_yaml_module():
    try:
        import yaml
    except ImportError as e:
        raise click.ClickException("The 'deepcell' command requires PyYAML.") from e

    return yaml


def _get_applications():
    deepcell_module = _get_deepcell_module()
    return {
        "mesmer": deepcell_module.Application.MESMER,
    }


try:
    from .. import deepcell as _deepcell_probe

    deepcell_cli_available = bool(getattr(_deepcell_probe, "deepcell_available", False))
except ImportError:
    deepcell_cli_available = False


@click.command(name="deepcell", help="Run an object segmentation batch using DeepCell")
@click.option(
    "--app",
    "application_name",
    type=click.Choice(["mesmer"], case_sensitive=True),
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
    help="Path/name of custom Keras model",
)
@click.option(
    "--modeldir",
    "keras_model_dir",
    type=click.Path(file_okay=False),
    default="/opt/keras/models",
    show_default=True,
    help="Path to Keras model directory",
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
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def deepcell_cmd(
    application_name,
    model_path_or_name,
    keras_model_dir,
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
    deepcell = _get_deepcell_module()
    applications = _get_applications()

    channel_groups = None
    if Path(panel_file).is_file():
        panel = io.read_panel(panel_file)
        if "deepcell" in panel and panel["deepcell"].notna().any():
            channel_groups = panel["deepcell"].values

    try:
        aggr_func = getattr(np, aggr_func_name)
    except AttributeError as e:
        raise click.ClickException(f"Invalid numpy aggregation function: {aggr_func_name}") from e

    img_files = io.list_image_files(img_dir)

    model = None
    if model_path_or_name is not None:
        try:
            from tensorflow.keras.models import load_model  # type: ignore
        except ImportError as e:
            raise click.ClickException("TensorFlow/Keras is required to load a DeepCell model.") from e

        model_path = Path(model_path_or_name)
        keras_model_path = Path(keras_model_dir).joinpath(model_path_or_name)

        if model_path.exists():
            model = load_model(model_path, compile=False)
        elif keras_model_path.exists():
            model = load_model(keras_model_path, compile=False)

    preprocess_kwargs = None
    if preprocess_file is not None:
        yaml = _get_yaml_module()
        with Path(preprocess_file).open() as f:
            preprocess_kwargs = yaml.load(f, yaml.Loader)

    postprocess_kwargs = None
    if postprocess_file is not None:
        yaml = _get_yaml_module()
        with Path(postprocess_file).open() as f:
            postprocess_kwargs = yaml.load(f, yaml.Loader)

    Path(mask_dir).mkdir(exist_ok=True)

    for img_file, mask in deepcell.try_segment_objects(
        img_files,
        applications[application_name],
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
        mask_file = io._as_path_with_suffix(Path(mask_dir) / img_file.name, ".tiff")
        io.write_mask(mask, mask_file)
        logger.info(mask_file)
