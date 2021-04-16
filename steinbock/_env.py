import os

from typing import Dict

ilastik_binary = "/opt/ilastik/run_ilastik.sh"
cellprofiler_binary = "cellprofiler"
cellprofiler_plugin_dir = "/opt/cellprofiler_plugins"


def check_x11():
    if "DISPLAY" not in os.environ:
        return "X11 required - did you set $DISPLAY?"
    if not os.path.exists("/tmp/.X11-unix"):
        return "X11 required - did you mount /tmp/.X11-unix"
    xauthority_path = os.path.expanduser("~/.Xauthority")
    if not os.path.exists(xauthority_path):
        return f"X11 required - did you mount {xauthority_path}?"
    return None


def get_ilastik_env() -> Dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    return env
