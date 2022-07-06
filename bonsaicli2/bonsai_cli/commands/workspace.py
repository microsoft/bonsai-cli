"""
This file contains the code for commands to read the workspace in the currently active config profile.
This functionality is neither supported nor documented. This command group exists to demonstrate the
operation of BonsaiApi.get_workspace() and BonsaiApi.get_workspace_resources().
"""
__author__ = "Robert Denkewalter"
__copyright__ = "Copyright 2022, Microsoft Corp."

import click
from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_not_found_as_click_exception,
)


@click.group(hidden=True)
def workspace():
    """workspace operations."""
    pass


@click.command("show", short_help="Describe the workspace")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.pass_context
def workspace_show(
    ctx: click.Context,
    workspace_id: str,
):
    try:
        response = api(use_aad=True).get_workspace(workspace_id)
        click.echo("{}".format(response))

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                False,
                "",
                "Show workspace",
                "workspace",
                workspace_id,
                False,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(False, "", False, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)


@click.command("resources", short_help="Describe the workspace provisioned resources")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.pass_context
def workspace_resources(
    ctx: click.Context,
    workspace_id: str,
):
    try:
        response = api(use_aad=True).get_workspace_resources(workspace_id)
        click.echo("{}".format(response))

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                False,
                "",
                "Show workspace",
                "workspace",
                workspace_id,
                False,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(False, "", False, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)


workspace.add_command(workspace_show)
workspace.add_command(workspace_resources)
