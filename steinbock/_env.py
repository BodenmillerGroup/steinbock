import logging
import os
import selectors
import subprocess
import sys
from functools import wraps
from pathlib import Path

logger = logging.getLogger(__name__.rpartition(".")[0])


def run_captured(args, **popen_kwargs) -> subprocess.CompletedProcess:
    with subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **popen_kwargs
    ) as process:
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)  # type: ignore
        selector.register(process.stderr, selectors.EVENT_READ)  # type: ignore
        running = True
        while running:
            for key, _ in selector.select():
                data = key.fileobj.read1()  # type: ignore
                if not data:
                    running = False
                elif key.fileobj is process.stdout:
                    sys.stdout.buffer.write(data)
                elif key.fileobj is process.stderr:
                    sys.stderr.buffer.write(data)
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
