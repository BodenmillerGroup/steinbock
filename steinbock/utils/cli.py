import click

from collections import OrderedDict

default_img_dir = "img"
default_panel_file = "panel.csv"
default_mask_dir = "masks"
default_cell_intensities_dir = "cell_intensities"
default_combined_cell_data_file = "cell_intensities.csv"
default_cell_dist_dir = "cell_distances"
default_graph_dir = "graphs"


class OrderedClickGroup(click.Group):
    def __init__(self, *args, commands=None, **kwargs):
        super(OrderedClickGroup, self).__init__(*args, **kwargs)
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands
