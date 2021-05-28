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
from steinbock.tools.data._cli import data_cmd_group
from steinbock.tools.masks._cli import masks_cmd_group
from steinbock.tools.mosaics._cli import mosaics_cmd_group


@click.group(
    name="tools",
    cls=cli.OrderedClickGroup,
    help="Various tools and applications",
)
def tools_cmd_group():
    pass


tools_cmd_group.add_command(data_cmd_group)
tools_cmd_group.add_command(masks_cmd_group)
tools_cmd_group.add_command(mosaics_cmd_group)


@tools_cmd_group.command(
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


@tools_cmd_group.command(
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
