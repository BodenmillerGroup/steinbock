import click

from steinbock import cli
from steinbock.preprocessing.imc import imc
from steinbock.preprocessing.imc._cli import imc_cmd_group


@click.group(
    name="preprocess",
    cls=cli.OrderedClickGroup,
    help="Extract and preprocess images from raw data",
)
def preprocess_cmd_group():
    pass


if imc.available:
    preprocess_cmd_group.add_command(imc_cmd_group)
