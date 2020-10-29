"""
This file contains the code for commands that target a bonsai exported brain in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

import click
from json import dumps

from bonsai_cli.api import BrainServerError
from bonsai_cli.exceptions import AuthenticationError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_unique_constraint_violation_as_click_exception,
    raise_not_found_as_click_exception,
)


@click.group(hidden=True)
def exportedbrain():
    """Exported brain operations."""
    pass


@click.command("create", short_help="Create an exported brain.")
@click.pass_context
@click.option("--name", "-n", help="[Required] Name of the exported brain.")
@click.option("--display-name", "-dn", help="Display name of the exported brain.")
@click.option("--description", "-des", help="Description for the exported brain.")
@click.option(
    "--processor-architecture",
    "-pa",
    help="Processor architecture for the exported brain. (Note: arm32v7 and arm64v8 processor architectures are only available for Linux exported brains.)",
    type=click.Choice(["x64", "arm32v7", "arm64v8"]),
    default="x64",
)
@click.option(
    "--brain-name", "-bn", help="[Required] Name of the brain to be exported."
)
@click.option(
    "--brain-version", "-bv", help="[Required] Version of the brain to be exported"
)
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--debug", default=False, is_flag=True, help="Verbose logging for request."
)
@click.option("--output", "-o", help="Set output, only json supported.")
@click.option(
    "--test",
    default=False,
    is_flag=True,
    help="Enhanced response for testing.",
    hidden=True,
)
@click.option(
    "--os-type",
    "-os",
    help="Operating system type for the exported brain container.  (Note: Windows exported brains are only available for the x64 processor architecture.)",
    type=click.Choice(["linux", "windows"]),
    default="linux",
)
def create_exportedbrain(
    ctx: click.Context,
    name: str,
    display_name: str,
    description: str,
    processor_architecture: str,
    brain_name: str,
    brain_version: int,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
    os_type: str,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the exported brain is required")

    if not name:
        raise_as_click_exception("Name of the brain to be exported is required")

    if not brain_version:
        raise_as_click_exception("Version of the brain to be exported is required")

    if os_type == "windows" and processor_architecture != "x64":
        raise_as_click_exception("Only x64 is supported for Windows exported brains")

    try:
        response = api(use_aad=True).create_exported_brain(
            name,
            display_name=display_name,
            description=description,
            processor_architecture=processor_architecture,
            os_type=os_type,
            brain_name=brain_name,
            brain_version=brain_version,
            workspace=workspace_id,
            debug=debug,
        )
    except BrainServerError as e:
        if "Unique index constraint violation" in str(e):
            raise_unique_constraint_violation_as_click_exception(
                debug, output, "Exported brain", name, test, e
            )
        else:
            raise_as_click_exception(e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "{} created.".format(response["name"])

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("list", short_help="Lists exported brains owned by current user.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--debug", default=False, is_flag=True, help="Verbose logging for request."
)
@click.option("--output", "-o", help="Set output, only json supported.")
@click.option(
    "--test",
    default=False,
    is_flag=True,
    help="Enhanced response for testing.",
    hidden=True,
)
@click.pass_context
def list_exportedbrain(
    ctx: click.Context, workspace_id: str, debug: bool, output: str, test: bool
):
    version_checker = get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_exported_brain(
            workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if len(response["value"]) == 0:
        click.echo("No exported brains exist for the current user")
        ctx.exit()

    if output == "json":
        if test:
            response["elapsed"] = str(response["elapsed"])
            response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(response, indent=4))

    else:
        for brain in response["value"]:
            click.echo(brain["name"])

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about an exported_brain.")
@click.option("--name", "-n", help="[Required] Name of the exported brain.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--debug", default=False, is_flag=True, help="Verbose logging for request."
)
@click.option("--output", "-o", help="Set output, only json supported.")
@click.option(
    "--test",
    default=False,
    is_flag=True,
    help="Enhanced response for testing.",
    hidden=True,
)
@click.pass_context
def show_exportedbrain(
    ctx: click.Context,
    name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the exported brain is required")

    try:
        response = api(use_aad=True).get_exported_brain(
            name, workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        if "not found" in str(e):
            raise_not_found_as_click_exception(
                debug, output, "show", "exported brain", name, test, e
            )

        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if output == "json":
        json_response = {
            "name": response["name"],
            "displayName": response["displayName"],
            "description": response["description"],
            "createdOn": response["createdTimeStamp"],
            "modifiedOn": response["modifiedTimeStamp"],
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": "",
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo("Name: {}".format(response["name"]))
        click.echo("Display Name: {}".format(response["displayName"]))
        click.echo("Description: {}".format(response["description"]))
        click.echo("Created On: {}".format(response["createdTimeStamp"]))
        click.echo("Modified On: {}".format(response["modifiedTimeStamp"]))

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("update", short_help="Update information about an exported brain.")
@click.option("--name", "-n", help="[Required] Name of the exported brain.")
@click.option("--display-name", "-dn", help="Display name for the exported brain.")
@click.option("--description", "-des", help="Description for the exported brain.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--debug", default=False, is_flag=True, help="Verbose logging for request."
)
@click.option("--output", "-o", help="Set output, only json supported.")
@click.option(
    "--test",
    default=False,
    is_flag=True,
    help="Enhanced response for testing.",
    hidden=True,
)
@click.pass_context
def update_exportedbrain(
    ctx: click.Context,
    name: str,
    display_name: str,
    description: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the exported brain is required")

    try:
        response = api(use_aad=True).update_exported_brain(
            name,
            display_name=display_name,
            description=description,
            workspace=workspace_id,
            debug=debug,
        )

    except BrainServerError as e:
        if "not found" in str(e):
            raise_not_found_as_click_exception(
                debug, output, "update", "exported brain", name, test, e
            )

        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "{} updated.".format(response["name"])

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("delete", short_help="Delete an exported brain.")
@click.option("--name", "-n", help="[Required] Name of the exported brain.")
@click.option(
    "--yes", "-y", default=False, is_flag=True, help="Do not prompt for confirmation."
)
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--debug", default=False, is_flag=True, help="Verbose logging for request."
)
@click.option("--output", "-o", help="Set output, only json supported.")
@click.option(
    "--test",
    default=False,
    is_flag=True,
    help="Enhanced response for testing.",
    hidden=True,
)
@click.pass_context
def delete_exportedbrain(
    ctx: click.Context,
    name: str,
    yes: bool,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the exported brain is required")

    is_delete = False

    if yes:
        is_delete = True

    if not yes:
        click.echo(
            "Are you sure you want to delete EXPORTED brain {} (y/n?).".format(name)
        )
        choice = input().lower()

        yes_set = {"yes", "y"}
        no_set = {"no", "n"}

        if choice in yes_set:
            is_delete = True
        elif choice in no_set:
            is_delete = False
        else:
            raise_as_click_exception("\nPlease respond with 'y' or 'n'")

    if is_delete:
        try:
            response = api(use_aad=True).delete_exported_brain(
                name, workspace=workspace_id, debug=debug
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        status_message = "{} deleted.".format(name)

        if output == "json":
            json_response = {
                "status": response["status"],
                "statusCode": response["statusCode"],
                "statusMessage": status_message,
            }

            if test:
                json_response["elapsed"] = str(response["elapsed"])
                json_response["timeTaken"] = str(response["timeTaken"])

            click.echo(dumps(json_response, indent=4))

        else:
            click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


exportedbrain.add_command(create_exportedbrain)
exportedbrain.add_command(show_exportedbrain)
exportedbrain.add_command(update_exportedbrain)
exportedbrain.add_command(list_exportedbrain)
exportedbrain.add_command(delete_exportedbrain)
