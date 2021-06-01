import click

from steinbock._cli.utils import OrderedClickGroup
from steinbock.classification._cli.ilastik import ilastik_cmd_group


@click.group(
    name="classify",
    cls=OrderedClickGroup,
    help="Perform pixel classification to extract probabilities",
)
def classify_cmd_group():
    pass


classify_cmd_group.add_command(ilastik_cmd_group)
