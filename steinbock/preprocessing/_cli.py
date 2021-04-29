import click

from steinbock import cli
from steinbock.preprocessing.imc._cli import imc_cmd


@click.group(
    cls=cli.OrderedClickGroup,
    help="Extract and preprocess images from raw data",
)
def preprocess():
    pass


preprocess.add_command(imc_cmd)
