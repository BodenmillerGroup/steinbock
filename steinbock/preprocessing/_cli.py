import click

from steinbock.preprocessing.imc._cli import imc_cmd
from steinbock.utils import cli


@click.group(
    cls=cli.OrderedClickGroup,
    help="Extract and preprocess images from raw data",
)
def preprocess():
    pass


preprocess.add_command(imc_cmd)
