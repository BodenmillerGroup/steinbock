import click

from steinbock.preprocessing._cli import preprocess
from steinbock.classification._cli import classify
from steinbock.segmentation._cli import segment
from steinbock.measurement._cli import measure
from steinbock.graphs._cli import graphs
from steinbock.utils import cli


@click.group(cls=cli.OrderedClickGroup)
def steinbock():
    pass


steinbock.add_command(preprocess)
steinbock.add_command(classify)
steinbock.add_command(segment)
steinbock.add_command(measure)
steinbock.add_command(graphs)
