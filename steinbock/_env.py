import click
import os
import subprocess
import sys

from functools import wraps
from pathlib import Path

from steinbock._version import version as steinbock_version

ilastik_binary = "/opt/ilastik/run_ilastik.sh"
cellprofiler_binary = "cellprofiler"
cellprofiler_plugin_dir = "/opt/cellprofiler_plugins"
keras_models_dir = "/opt/keras/models"


def run_captured(args, *popen_args, file=sys.stdout, **popen_kwargs):
    with subprocess.Popen(
        args,
        *popen_args,
        bufsize=0,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **popen_kwargs,
    ) as process:
        for c in iter(lambda: process.stdout.read(1), b""):
            file.buffer.write(c)
        process.wait()
    return subprocess.CompletedProcess(
        process.args, process.returncode, process.stdout, process.stderr
    )


def check_x11(func):
    @wraps(func)
    def check_x11_wrapper(*args, **kwargs):
        display_var = "DISPLAY"
        if display_var not in os.environ:
            click.echo(
                f"WARNING: X11 required; did you set ${display_var}?",
                file=sys.stderr,
            )
        x11_path = Path("/tmp/.X11-unix")
        if not x11_path.exists():
            click.echo(
                f"WARNING: X11 required; did you mount {x11_path}?",
                file=sys.stderr,
            )
        xauth_path = Path("~/.Xauthority").expanduser()
        if not xauth_path.exists():
            click.echo(
                f"WARNING: X11 required; did you mount {xauth_path}?",
                file=sys.stderr,
            )
        return func(*args, **kwargs)

    return check_x11_wrapper


def use_ilastik_env(func):
    @wraps(func)
    def use_ilastik_env_wrapper(*args, **kwargs):
        if "ilastik_env" not in kwargs:
            kwargs["ilastik_env"] = os.environ.copy()
        kwargs["ilastik_env"].pop("PYTHONPATH", None)
        kwargs["ilastik_env"].pop("PYTHONHOME", None)
        return func(*args, **kwargs)

    return use_ilastik_env_wrapper


def check_steinbock_version(func):
    @wraps(func)
    def check_steinbock_version_wrapper(*args, **kwargs):
        if Path(".steinbock_version").exists():
            saved_steinbock_version = (
                Path(".steinbock_version").read_text(encoding="utf-8").strip()
            )
            if saved_steinbock_version != steinbock_version:
                click.echo(
                    "WARNING: steinbock version change detected!\n"
                    f"    previous: {saved_steinbock_version}\n"
                    f"    current: {steinbock_version}",
                    file=sys.stderr,
                )
        else:
            Path(".steinbock_version").write_text(
                steinbock_version, encoding="utf-8"
            )
        return func(*args, **kwargs)

    return check_steinbock_version_wrapper
