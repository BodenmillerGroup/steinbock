import click

from steinbock import cli
from steinbock.segmentation.cellprofiler._cli import cellprofiler_cmd


@click.group(
    cls=cli.OrderedClickGroup,
    help="Perform image segmentation to create object masks",
)
def segment():
    pass


segment.add_command(cellprofiler_cmd)
