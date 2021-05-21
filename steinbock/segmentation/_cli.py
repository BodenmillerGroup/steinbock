import click

from pathlib import Path

from steinbock import cli, io
from steinbock._env import check_version
from steinbock.segmentation import deepcell
from steinbock.segmentation.cellprofiler._cli import cellprofiler_cmd


@click.group(
    cls=cli.OrderedClickGroup,
    help="Perform image segmentation to create object masks",
)
def segment():
    pass


@segment.command(
    name="deepcell",
    help="Run a object segmentation batch using DeepCell",
)
@click.option(
    "--app"
    "application",
    type=click.Choice(
        [deepcell.Application.MESMER.value],
        case_sensitive=False,
    ),
    required=True,
    show_choices=True,
    help="DeepCell application name",
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
    type=click.Option(["whole-cell", "nuclear"]),
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
    application,
    img_dir,
    panel_file,
    minmax,
    zscore,
    pixel_size_um,
    segmentation_type,
    mask_dir,
):
    img_files = io.list_images(img_dir)
    channel_groups = None
    if Path(panel_file).exists():
        panel = io.read_panel(panel_file)
        if deepcell.panel_deepcell_col in panel:
            channel_groups = panel[deepcell.panel_deepcell_col].values
    Path(mask_dir).mkdir(exist_ok=True)
    for img_file, mask in deepcell.segment_objects(
        img_files,
        deepcell.Application(application),
        model=None,  # TODO store model in Docker container
        channelwise_minmax=minmax,
        channelwise_zscore=zscore,
        channel_groups=channel_groups,
        pixel_size_um=pixel_size_um,
        segmentation_type=segmentation_type,
    ):
        mask_file = io.write_mask(mask, Path(mask_dir) / img_file.stem)
        print(mask_file)


segment.add_command(cellprofiler_cmd)
