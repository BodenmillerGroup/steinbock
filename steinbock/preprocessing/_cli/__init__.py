import click

from .external import external_cmd_group
from .imc import imc_cli_available, imc_cmd_group
from ..._cli.utils import OrderedClickGroup


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
