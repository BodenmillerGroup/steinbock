import click

from collections import OrderedDict

default_img_dir = "img"
default_mask_dir = "masks"
default_panel_file = "panel.csv"
default_dists_dir = "object_dists"
default_graph_dir = "object_graphs"
default_intensities_dir = "object_intensities"
default_regionprops_dir = "object_regionprops"
default_combined_data_csv_file = "objects.csv"
default_combined_data_fcs_file = "objects.fcs"
default_ome_dir = "ome"


class OrderedClickGroup(click.Group):
    def __init__(self, *args, commands=None, **kwargs):
        super(OrderedClickGroup, self).__init__(*args, **kwargs)
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands
