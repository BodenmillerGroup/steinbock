import click

from steinbock import cli
from steinbock.classification.ilastik._cli import ilastik_cmd_group


@click.group(
    name="classify",
    cls=cli.OrderedClickGroup,
    help="Perform pixel classification to extract probabilities",
)
def classify_cmd_group():
    pass


classify_cmd_group.add_command(ilastik_cmd_group)
