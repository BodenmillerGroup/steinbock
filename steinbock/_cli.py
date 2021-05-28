import click
import sys

from steinbock import cli, utils
from steinbock._env import (
    cellprofiler_binary,
    cellprofiler_plugin_dir,
    check_version,
    check_x11,
    ilastik_binary,
    ilastik_env,
)
from steinbock.preprocessing._cli import preprocess_cmd_group
from steinbock.classification._cli import classify_cmd_group
from steinbock.segmentation._cli import segment_cmd_group
from steinbock.measurement._cli import measure_cmd_group
from steinbock.export._cli import export_cmd_group
from steinbock.tools._cli import tools_cmd_group
from steinbock.version import version


@click.group(
    name="steinbock",
    cls=cli.OrderedClickGroup,
)
@click.version_option(version)
def steinbock_cmd_group():
    pass


steinbock_cmd_group.add_command(preprocess_cmd_group)
steinbock_cmd_group.add_command(classify_cmd_group)
steinbock_cmd_group.add_command(segment_cmd_group)
steinbock_cmd_group.add_command(measure_cmd_group)
steinbock_cmd_group.add_command(export_cmd_group)
steinbock_cmd_group.add_command(tools_cmd_group)


@steinbock_cmd_group.group(
    name="apps",
    cls=cli.OrderedClickGroup,
    help="Third-party applications",
)
def apps_cmd_group():
    pass


@apps_cmd_group.command(
    name="ilastik",
    context_settings={"ignore_unknown_options": True},
    help="Run Ilastik (GUI requires X11)",
    add_help_option=False,
)
@click.argument(
    "ilastik_args",
    nargs=-1,
    type=click.UNPROCESSED,
)
@check_version
@check_x11
@ilastik_env
def ilastik_cmd(ilastik_args, env):
    args = [ilastik_binary] + list(ilastik_args)
    result = utils.run_captured(args, env=env)
    sys.exit(result.returncode)


@apps_cmd_group.command(
    name="cellprofiler",
    context_settings={"ignore_unknown_options": True},
    help="Run CellProfiler (GUI requires X11)",
    add_help_option=False,
)
@click.argument(
    "cellprofiler_args",
    nargs=-1,
    type=click.UNPROCESSED,
)
@check_version
@check_x11
def cellprofiler_cmd(cellprofiler_args):
    args = [cellprofiler_binary] + list(cellprofiler_args)
    if not any(arg.startswith("--plugins-directory") for arg in args):
        args.append(f"--plugins-directory={cellprofiler_plugin_dir}")
    result = utils.run_captured(args)
    sys.exit(result.returncode)
