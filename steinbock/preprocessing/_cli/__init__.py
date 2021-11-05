import click

from steinbock._cli.utils import OrderedClickGroup
from steinbock.preprocessing._cli.external import external_cmd_group
from steinbock.preprocessing._cli.imc import imc_cli_available, imc_cmd_group


@click.group(
    name="preprocess",
    cls=OrderedClickGroup,
    help="Extract and preprocess images from raw data",
)
def preprocess_cmd_group():
    pass


if imc_cli_available:
    preprocess_cmd_group.add_command(imc_cmd_group)

preprocess_cmd_group.add_command(external_cmd_group)
