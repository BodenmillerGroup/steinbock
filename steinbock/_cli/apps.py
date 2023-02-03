import sys
from pathlib import Path

import click
import click_log

from .._env import run_captured, use_ilastik_env
from .._steinbock import SteinbockException
from .._steinbock import logger as steinbock_logger
from .utils import OrderedClickGroup, catch_exception


@click.group(name="apps", cls=OrderedClickGroup, help="Third-party applications")
def apps_cmd_group():
    pass


@apps_cmd_group.command(
    name="ilastik",
    context_settings={"ignore_unknown_options": True},
    help="Run Ilastik GUI",
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
@use_ilastik_env
def ilastik_cmd(ilastik_binary, ilastik_args, ilastik_env):
    args = [ilastik_binary] + list(ilastik_args)
    result = run_captured(args, env=ilastik_env)
    sys.exit(result.returncode)


@apps_cmd_group.command(
    name="cellprofiler",
    context_settings={"ignore_unknown_options": True},
    help="Run CellProfiler GUI",
    add_help_option=False,
)
@click.option(
    "--python",
    "python_path",
    type=click.Path(dir_okay=False),
    default="/opt/cellprofiler-venv/bin/python",
    show_default=True,
    help="Python path",
)
@click.option(
    "--cellprofiler",
    "cellprofiler_module",
    type=click.STRING,
    default="cellprofiler",
    show_default=True,
    help="CellProfiler module",
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
def cellprofiler_cmd(
    python_path, cellprofiler_module, cellprofiler_plugin_dir, cellprofiler_args
):
    args = [python_path, "-m", cellprofiler_module] + list(cellprofiler_args)
    if Path(cellprofiler_plugin_dir).is_dir():
        args.append(f"--plugins-directory={cellprofiler_plugin_dir}")
    result = run_captured(args)
    sys.exit(result.returncode)


@apps_cmd_group.command(
    name="jupyter",
    context_settings={"ignore_unknown_options": True},
    help="Run Jupyter Notebook",
    add_help_option=False,
)
@click.option(
    "--python",
    "python_path",
    type=click.Path(dir_okay=False),
    default="python",
    show_default=True,
    help="Python path",
)
@click.option(
    "--jupyter",
    "jupyter_module",
    type=click.STRING,
    default="jupyter",
    show_default=True,
    help="Jupyter module",
)
@click.argument("jupyter_args", nargs=-1, type=click.UNPROCESSED)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def jupyter_cmd(python_path, jupyter_module, jupyter_args):
    jupyter_args = list(jupyter_args)
    if not any(arg.startswith("--ip=") for arg in jupyter_args):
        jupyter_args.append("--ip='0.0.0.0'")
    args = [python_path, "-m", jupyter_module, "notebook"] + jupyter_args
    result = run_captured(args)
    sys.exit(result.returncode)


@apps_cmd_group.command(
    name="jupyterlab",
    context_settings={"ignore_unknown_options": True},
    help="Run Jupyter Lab",
    add_help_option=False,
)
@click.option(
    "--python",
    "python_path",
    type=click.Path(dir_okay=False),
    default="python",
    show_default=True,
    help="Python path",
)
@click.option(
    "--jupyter",
    "jupyter_module",
    type=click.STRING,
    default="jupyter",
    show_default=True,
    help="Jupyter module",
)
@click.argument("jupyterlab_args", nargs=-1, type=click.UNPROCESSED)
@click_log.simple_verbosity_option(logger=steinbock_logger)
@catch_exception(handle=SteinbockException)
def jupyterlab_cmd(python_path, jupyter_module, jupyterlab_args):
    jupyterlab_args = list(jupyterlab_args)
    if not any(arg.startswith("--ip=") for arg in jupyterlab_args):
        jupyterlab_args.append("--ip='0.0.0.0'")
    args = [python_path, "-m", jupyter_module, "lab"] + jupyterlab_args
    result = run_captured(args)
    sys.exit(result.returncode)
