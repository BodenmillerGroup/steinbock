import click

from steinbock.classification.ilastik._cli import ilastik_cmd
from steinbock.utils import cli


@click.group(
    cls=cli.OrderedClickGroup,
    help="Perform pixel classification to extract probabilities",
)
def classify():
    pass


classify.add_command(ilastik_cmd)
