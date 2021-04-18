import click
import sys

from steinbock._env import (
    check_x11,
    ilastik_binary,
    get_ilastik_env,
    cellprofiler_binary,
    cellprofiler_plugin_dir,
)
from steinbock.tools.mosaic._cli import mosaic_cmd
from steinbock.utils import cli, system


@click.group(
    name="tools",
    cls=cli.OrderedClickGroup,
    help="Various tools and applications",
)
def tools():
    pass


@tools.command(
    context_settings={"ignore_unknown_options": True},
    help="Run the Ilastik application (GUI mode requires X11)",
    add_help_option=False,
)
@click.argument(
    "ilastik_args",
    nargs=-1,
    type=click.UNPROCESSED,
)
def ilastik(ilastik_args):
    x11_warning_message = check_x11()
    if x11_warning_message is not None:
        click.echo(x11_warning_message, file=sys.stderr)
    args = [ilastik_binary] + list(ilastik_args)
    result = system.run_captured(args, env=get_ilastik_env())
    sys.exit(result.returncode)


@tools.command(
    context_settings={"ignore_unknown_options": True},
    help="Run the CellProfiler application (GUI mode requires X11)",
    add_help_option=False,
)
@click.argument(
    "cellprofiler_args",
    nargs=-1,
    type=click.UNPROCESSED,
)
def cellprofiler(cellprofiler_args):
    x11_warning_message = check_x11()
    if x11_warning_message is not None:
        click.echo(x11_warning_message, file=sys.stderr)
    args = [cellprofiler_binary] + list(cellprofiler_args)
    if not any(arg.startswith("--plugins-directory") for arg in args):
        args.append(f"--plugins-directory={cellprofiler_plugin_dir}")
    result = system.run_captured(args)
    sys.exit(result.returncode)


tools.add_command(mosaic_cmd)
