import click
import sys

from steinbock._cli.utils import OrderedClickGroup
from steinbock._env import (
    cellprofiler_binary,
    cellprofiler_plugin_dir,
    check_steinbock_version,
    check_x11,
    ilastik_binary,
    run_captured,
    use_ilastik_env,
)


@click.group(
    name="apps", cls=OrderedClickGroup, help="Third-party applications"
)
def apps_cmd_group():
    pass


@apps_cmd_group.command(
    name="ilastik",
    context_settings={"ignore_unknown_options": True},
    help="Run Ilastik (GUI requires X11)",
    add_help_option=False,
)
@click.argument("ilastik_args", nargs=-1, type=click.UNPROCESSED)
@check_steinbock_version
@check_x11
@use_ilastik_env
def ilastik_cmd(ilastik_args, ilastik_env):
    args = [ilastik_binary] + list(ilastik_args)
    result = run_captured(args, env=ilastik_env)
    sys.exit(result.returncode)


@apps_cmd_group.command(
    name="cellprofiler",
    context_settings={"ignore_unknown_options": True},
    help="Run CellProfiler (GUI requires X11)",
    add_help_option=False,
)
@click.argument("cellprofiler_args", nargs=-1, type=click.UNPROCESSED)
@check_steinbock_version
@check_x11
def cellprofiler_cmd(cellprofiler_args):
    args = [cellprofiler_binary] + list(cellprofiler_args)
    if not any(arg.startswith("--plugins-directory") for arg in args):
        args.append(f"--plugins-directory={cellprofiler_plugin_dir}")
    result = run_captured(args)
    sys.exit(result.returncode)
