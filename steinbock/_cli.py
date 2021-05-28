import click

from steinbock import cli
from steinbock.preprocessing._cli import preprocess_cmd_group
from steinbock.classification._cli import classify_cmd_group
from steinbock.segmentation._cli import segment_cmd_group
from steinbock.measurement._cli import measure_cmd_group
from steinbock.tools._cli import tools_cmd_group


@click.group(
    name="steinbock",
    cls=cli.OrderedClickGroup,
)
def steinbock_cmd_group():
    pass


steinbock_cmd_group.add_command(preprocess_cmd_group)
steinbock_cmd_group.add_command(classify_cmd_group)
steinbock_cmd_group.add_command(segment_cmd_group)
steinbock_cmd_group.add_command(measure_cmd_group)
steinbock_cmd_group.add_command(tools_cmd_group)
