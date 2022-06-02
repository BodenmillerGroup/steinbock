import os
import logging
import subprocess
import sys
from functools import wraps
from pathlib import Path


logger = logging.getLogger(__name__.rpartition(".")[0])


def run_captured(
    args, *popen_args, file=sys.stdout, **popen_kwargs
) -> subprocess.CompletedProcess:
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
        if "DISPLAY" not in os.environ:
            logger.warning("X11 required; did you set $DISPLAY?")
        x11_path = Path("/tmp/.X11-unix")
        if not x11_path.exists():
            logger.warning(f"X11 required; did you bind-mount {x11_path}?")
        xauth_path = Path("~/.Xauthority").expanduser()
        if not xauth_path.exists():
            logger.warning(f"X11 required; did you bind-mount {xauth_path}?")
        return func(*args, **kwargs)

    return check_x11_wrapper


def use_ilastik_env(func):
    @wraps(func)
    def use_ilastik_env_wrapper(*args, **kwargs):
        if "ilastik_env" not in kwargs:
            kwargs["ilastik_env"] = os.environ.copy()
        kwargs["ilastik_env"].pop("PYTHONPATH", None)
        kwargs["ilastik_env"].pop("PYTHONHOME", None)
        kwargs["ilastik_env"].pop("LD_LIBRARY_PATH", None)
        return func(*args, **kwargs)

    return use_ilastik_env_wrapper
