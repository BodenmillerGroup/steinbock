import subprocess
import sys


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
