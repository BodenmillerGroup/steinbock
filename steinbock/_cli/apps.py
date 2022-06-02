import sys
from pathlib import Path

import click
import click_log

from .._env import check_x11, run_captured, use_ilastik_env
from .._steinbock import SteinbockException
from .._steinbock import logger as steinbock_logger
from .utils import OrderedClickGroup, catch_exception


@click.group(name="apps", cls=OrderedClickGroup, help="Third-party applications")
def apps_cmd_group():
    pass


@apps_cmd_group.command(
    name="ilastik",
    context_settings={"ignore_unknown_options": True},
    help="Run Ilastik (GUI requires X11)",
    add_help_option=False,
)
@click.option(
    "--ilastik",
    "ilastik_binary",
    type=click.STRING,
    default="/opt/ilastik/run_ilastik.sh",
    show_default=True,
    help="Ilastik binary",
)
@click.argument("ilastik_args", nargs=-1, type=click.UNPROCESSED)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
@check_x11
@use_ilastik_env
def ilastik_cmd(ilastik_binary, ilastik_args, ilastik_env):
    args = [ilastik_binary] + list(ilastik_args)
    result = run_captured(args, env=ilastik_env)
    sys.exit(result.returncode)


@apps_cmd_group.command(
    name="cellprofiler",
    context_settings={"ignore_unknown_options": True},
    help="Run CellProfiler (GUI requires X11)",
    add_help_option=False,
)
@click.option(
    "--cellprofiler",
    "cellprofiler_binary",
    type=click.STRING,
    default="cellprofiler",
    show_default=True,
    help="CellProfiler binary",
)
@click.option(
    "--plugins-directory",
    "cellprofiler_plugin_dir",
    type=click.Path(file_okay=False),
    default="/opt/cellprofiler_plugins",
    show_default=True,
    help="Path to the CellProfiler plugin directory",
)
@click.argument("cellprofiler_args", nargs=-1, type=click.UNPROCESSED)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
@check_x11
def cellprofiler_cmd(cellprofiler_binary, cellprofiler_plugin_dir, cellprofiler_args):
    args = [cellprofiler_binary] + list(cellprofiler_args)
    if Path(cellprofiler_plugin_dir).exists():
        args.append(f"--plugins-directory={cellprofiler_plugin_dir}")
    result = run_captured(args)
    sys.exit(result.returncode)
