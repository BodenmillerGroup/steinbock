import click

from collections import OrderedDict

default_img_dir = "img"
default_mask_dir = "masks"
default_panel_file = "panel.csv"
default_combined_cell_data_file = "cells.csv"
default_cell_intensities_dir = "cell_intensities"
default_cell_regionprops_dir = "cell_regionprops"
default_cell_dists_dir = "cell_distances"
default_cell_graph_dir = "cell_graphs"


class OrderedClickGroup(click.Group):
    def __init__(self, *args, commands=None, **kwargs):
        super(OrderedClickGroup, self).__init__(*args, **kwargs)
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands
