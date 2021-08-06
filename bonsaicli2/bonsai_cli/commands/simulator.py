"""
This file contains the code for commands that target a bonsai simulator in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

import click

from .simulator_package import package
from .simulator_unmanaged import unmanaged


@click.group()
def simulator():
    """Simulator operations."""
    pass


simulator.add_command(package)
simulator.add_command(unmanaged)
