import click

from steinbock import cli
from steinbock.export.data._cli import data_cmd_group
from steinbock.export.images._cli import images_cmd_group
from steinbock.export.graphs._cli import graphs_cmd_group


@click.group(
    name="export",
    cls=cli.OrderedClickGroup,
    help="Export data to third-party formats",
)
def export_cmd_group():
    pass


export_cmd_group.add_command(images_cmd_group)
export_cmd_group.add_command(data_cmd_group)
export_cmd_group.add_command(graphs_cmd_group)
