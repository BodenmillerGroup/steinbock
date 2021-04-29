import click

from steinbock import cli
from steinbock.classification.ilastik._cli import ilastik_cmd


@click.group(
    cls=cli.OrderedClickGroup,
    help="Perform pixel classification to extract probabilities",
)
def classify():
    pass


classify.add_command(ilastik_cmd)
