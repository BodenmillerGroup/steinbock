import click

from collections import OrderedDict

default_img_dir = "img"
default_mask_dir = "masks"
default_panel_file = "panel.csv"
default_combined_data_file = "objects.csv"
default_intensities_dir = "intensities"
default_regionprops_dir = "regionprops"
default_distances_dir = "distances"
default_graph_dir = "graphs"


class OrderedClickGroup(click.Group):
    def __init__(self, *args, commands=None, **kwargs):
        super(OrderedClickGroup, self).__init__(*args, **kwargs)
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands
