import click

from steinbock import cli
from steinbock.export.data._cli import csv_cmd


@click.group(
    name="export",
    cls=cli.OrderedClickGroup,
    help="Export data to third-party formats",
)
def export_cmd_group():
    pass


export_cmd_group.add_command(csv_cmd)
