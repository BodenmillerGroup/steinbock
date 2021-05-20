import click
import os
import sys

from functools import wraps
from pathlib import Path

from steinbock.version import version

ilastik_binary = "/opt/ilastik/run_ilastik.sh"
cellprofiler_binary = "cellprofiler"
cellprofiler_plugin_dir = "/opt/cellprofiler_plugins"
version_file = ".steinbock_version"


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
        xauth_path = Path("~/.Xauthority")
        if not xauth_path.exists():
            click.echo(
                f"WARNING: X11 required; did you mount {xauth_path}?",
                file=sys.stderr,
            )
        return func(*args, **kwargs)

    return check_x11_wrapper


def ilastik_env(func):
    @wraps(func)
    def ilastik_env_wrapper(*args, **kwargs):
        if "env" not in kwargs:
            kwargs["env"] = os.environ.copy()
        kwargs["env"].pop("PYTHONPATH", None)
        kwargs["env"].pop("PYTHONHOME", None)
        return func(*args, **kwargs)

    return ilastik_env_wrapper


def check_version(func):
    @wraps(func)
    def check_version_wrapper(*args, **kwargs):
        if Path(version_file).exists():
            saved_version = Path(version_file).read_text(encoding="utf-8")
            if saved_version != version:
                click.echo(
                    "WARNING: steinbock version change detected!\n"
                    f"    previous: {saved_version}\n"
                    f"    current: {version}\n"
                    f"To disable this warning, edit the {version_file} file.",
                    file=sys.stderr,
                )
        else:
            Path(version_file).write_text(version, encoding="utf-8")
        return func(*args, **kwargs)

    return check_version_wrapper
