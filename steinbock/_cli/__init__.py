import click

from .._version import version as steinbock_version
from ..classification._cli import classify_cmd_group
from ..export._cli import export_cmd_group
from ..measurement._cli import measure_cmd_group
from ..preprocessing._cli import preprocess_cmd_group
from ..segmentation._cli import segment_cmd_group
from ..utils._cli import utils_cmd_group
from .apps import apps_cmd_group
from .utils import OrderedClickGroup


@click.group(name="steinbock", cls=OrderedClickGroup)
@click.version_option(steinbock_version)
def steinbock_cmd_group():
    pass


steinbock_cmd_group.add_command(preprocess_cmd_group)
steinbock_cmd_group.add_command(classify_cmd_group)
steinbock_cmd_group.add_command(segment_cmd_group)
steinbock_cmd_group.add_command(measure_cmd_group)
steinbock_cmd_group.add_command(export_cmd_group)
steinbock_cmd_group.add_command(utils_cmd_group)
steinbock_cmd_group.add_command(apps_cmd_group)
