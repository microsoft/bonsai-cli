"""
This file contains the code for commands that target a deploying a bonsai exported brain in version 2 of the bonsai command line.
"""
__author__ = "David Coe"
__copyright__ = "Copyright 2022, Microsoft Corp."

import click

from .deployment_webapp import webapp


@click.group(hidden=False)
def deployment():
    """Deploy operations."""
    pass


deployment.add_command(webapp)
