import os
import subprocess
import sys


def check_x11():
    if "DISPLAY" not in os.environ:
        return "X11 required - did you set $DISPLAY?"
    if not os.path.exists("/tmp/.X11-unix"):
        return "X11 required - did you mount /tmp/.X11-unix"
    xauthority_path = os.path.expanduser("~/.Xauthority")
    if not os.path.exists(xauthority_path):
        return f"X11 required - did you mount {xauthority_path}?"
    return None


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
        process.args,
        process.returncode,
        process.stdout,
        process.stderr,
    )
