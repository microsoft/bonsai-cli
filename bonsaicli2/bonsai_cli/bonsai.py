"""
This file contains the main code for version 2 of the bonsai command line,
the command line can be used to interact with the bonsai service.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

import platform
import pkg_resources
import pprint
import sys

import click
from json import dumps
from tabulate import tabulate
from typing import Any, Dict, Optional

from .logger import Logger
from .exceptions import AuthenticationError
from .api import BonsaiAPI, BrainServerError
from .config import Config
from .utils import (
    AsyncCliVersionChecker,
    api,
    NullCliVersionChecker,
    print_profile_information,
    list_profiles,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_unique_constraint_violation_as_click_exception,
    raise_not_found_as_click_exception,
    raise_client_side_click_exception
)

log = Logger()

""" Global variable for click context settings following the conventions
from the click documentation. It can be modified to add more context
settings if they are needed in future development of the cli.
"""
CONTEXT_SETTINGS: Dict[str, Any] = dict(help_option_names=["--help", "-h"])


def _version_callback(ctx: click.Context, param: click.Parameter, value: str):
    """
    This is the callback function when --version option
    is used. The function lets the user know what version
    of the cli they are currently on and if there is an
    update available.
    """
    if not value or ctx.resilient_parsing:
        return
    AsyncCliVersionChecker().check_cli_version(wait=True)
    ctx.exit()


def _sysinfo(ctx: click.Context, param: click.Parameter, value: str):
    if not value or ctx.resilient_parsing:
        return
    click.echo("\nPlatform Information\n--------------------")
    click.echo(sys.version)
    click.echo(platform.platform())
    packages = [d for d in iter(pkg_resources.working_set)]
    click.echo("\nPackage Information\n-------------------")
    click.echo(pprint.pformat(packages))
    click.echo("\nBonsai Profile Information\n--------------------------")
    print_profile_information(Config(use_aad=True))
    ctx.exit()


def _set_color(ctx: click.Context, param: click.Parameter, value: str):
    """ Set use_color flag in bonsai config """
    if value is None or ctx.resilient_parsing:
        return

    # no need for AAD authentication if only setting color
    config = Config(use_aad=False)
    if value:
        config.update(use_color=True)
    else:
        config.update(use_color=False)
    ctx.exit()


def _get_version_checker(ctx: click.Context, interactive: bool):
    """
    param ctx: Click context
    param interactive: True if the caller is interactive
    """
    if ctx.obj["VERSION_CHECK"] and interactive:
        return AsyncCliVersionChecker()
    else:
        return NullCliVersionChecker()


@click.group()
def brain():
    """Brain operations."""
    pass


@click.command("create", short_help="Create a brain.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--display-name", help="Display name of the brain.")
@click.option("--description", help="Description for the brain.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def create_brain(
    ctx: click.Context,
    name: str,
    display_name: str,
    description: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    try:
        response = api(use_aad=True).create_brain(
            name,
            display_name=display_name,
            description=description,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

    except BrainServerError as e:
        if "Unique index constraint violation" in str(e):
            raise_unique_constraint_violation_as_click_exception(
                debug, output, "Brain", name, test, e
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

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


@click.command("show", short_help="Show information about a brain.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def show_brain(
    ctx: click.Context,
    name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    try:
        response = api(use_aad=True).get_brain(
            name, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug, output, "Show brain", "Brain", name, test, e
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


@click.command("update", short_help="Update information about a brain.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--display-name", help="Display name of the brain.")
@click.option("--description", help="Description for the brain.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def update_brain(
    ctx: click.Context,
    name: str,
    display_name: str,
    description: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    try:
        response = api(use_aad=True).update_brain(
            name=name,
            display_name=display_name,
            description=description,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug, output, "Update brain", "Brain", name, test, e
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


@click.command("list", short_help="List brains owned by current user.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def list_brain(
    ctx: click.Context, workspace_id: str, debug: bool, output: str, test: bool
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_brains(
            workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if len(response["value"]) == 0:
        click.echo("No brains exist for the current user")
        ctx.exit()

    if output == "json":
        dict_rows = []
        for brain in response["value"]:
            dict_rows.append(brain["name"])

        json_response = {
            "value": dict_rows,
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": "",
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        for brain in response["value"]:
            click.echo(brain["name"])

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("delete", short_help="Delete a brain.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--yes", "-y", default=False, is_flag=True, help="Do not prompt for confirmation."
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def delete_brain(
    ctx: click.Context,
    name: str,
    yes: bool,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=True)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    is_delete = True

    if not yes:
        click.echo(
            "Are you sure you want to delete brain {} (y/n?).".format(name)
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
            response = api(use_aad=True).delete_brain(
                name, workspace=workspace_id, debug=debug
            )

            if response["statusCode"] ==204:
                raise_client_side_click_exception(debug, output, test, 204, "Brain '{}' not found".format(name), response)

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


@click.group("version", short_help="Brain version operations.")
def version():
    """
    brain version operations.
    """
    pass


@click.command("copy", short_help="Clone a brain version from an existing version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version", type=int,
    help="Provide the version of the brain to be copied, defaults to latest.",
)
@click.option("--notes", help="Notes to be added to the brain version.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def create_brain_version(
    ctx: click.Context,
    name: str,
    version: int,
    notes: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(name, "Copy brain version", debug, output, test)

    try:
        response = api(use_aad=True).create_brain_version(
            name,
            version,
            description=notes,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "Copied {} version {} to version {}.".format(
        name, response["sourceVersion"], response["version"]
    )

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


@click.command("show", short_help="Show information about a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to show, defaults to latest.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def show_brain_version(
    ctx: click.Context,
    name: str,
    version: int,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(name, "Show brain version", debug, output, test)

    try:
        response = api(use_aad=True).get_brain_version(
            name, version, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Show brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if output == "json":
        json_response = {
            "version": response["version"],
            "trainingState": response["state"],
            "assessmentState": response["assessmentState"],
            "notes": response["description"],
            "createdOn": response["createdOn"],
            "modifiedOn": response["modifiedOn"],
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": "",
        }

        if test:
            json_response["concepts"] = response["concepts"]
            json_response["simulators"] = response["simulators"]
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo("Version: {}".format(response["version"]))
        click.echo("Training State: {}".format(response["state"]))
        click.echo("Assessment State: {}".format(response["assessmentState"]))
        click.echo("Notes: {}".format(response["description"]))
        click.echo("Created On: {}".format(response["createdOn"]))
        click.echo("Modified On: {}".format(response["modifiedOn"]))

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("update", short_help="Update information about a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to update, defaults to latest.")
@click.option("--notes", help="Notes to be added to the brain version.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def update_brain_version(
    ctx: click.Context,
    name: str,
    version: int,
    notes: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(name, "Update brain version", debug, output, test)

    try:
        response = api(use_aad=True).update_brain_version_details(
            name,
            version=version,
            description=notes,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Update brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "Updated {} version {}.".format(name, response["version"])

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


@click.command("list", short_help="List versions of a brain.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def list_brain_version(
    ctx: click.Context,
    name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    try:
        response = api(use_aad=True).list_brain_versions(
            name, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "List brain version",
                "Brain",
                name,
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    rows = []
    dict_rows = []
    for item in response["value"]:
        try:
            version = item["version"]
            training_state = item["state"]
            assessment_state = item["assessmentState"]
            rows.append([version, training_state, assessment_state])
            dict_rows.append(
                {
                    "version": version,
                    "trainingState": training_state,
                    "assessmentState": assessment_state,
                }
            )
        except KeyError:
            pass  # If it's missing a field, ignore it.

    if output == "json":
        json_response = {
            "value": dict_rows,
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": "",
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        table = tabulate(
            rows,
            headers=["VERSION", "TRAINING STATE", "ASSESSMENT STATE"],
            tablefmt="orgtbl",
        )
        click.echo(table)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("delete", short_help="Delete a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to delete, defaults to latest.")
@click.option(
    "--yes", "-y", default=False, is_flag=True, help="Do not prompt for confirmation."
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def delete_brain_version(
    ctx: click.Context,
    name: str,
    version: int,
    yes: bool,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=True)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    is_delete = True

    if not yes:
        click.echo(
            "Are you sure you want to delete brain {} version {} (y/n?).".format(
                name, version
            )
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
        if not version:
            version = get_latest_brain_version(name, "Delete brain version", debug, output, test)

        try:
            response = api(use_aad=True).delete_brain_version(
                name, version=version, workspace=workspace_id, debug=debug
            )

            if response["statusCode"] ==204:
                raise_client_side_click_exception(debug, output, test, 204, "Brain '{}' version '{}' not found".format(name, version), response)

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        status_message = "Deleted {} version {}.".format(name, version)

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


@click.command("update-inkling", short_help="Update inkling of a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--file", "-f", help="[Required] Path to inkling file.")
@click.option("--version", type=int, help="Version to update inkling, defaults to latest.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def update_inkling(
    ctx: click.Context,
    name: str,
    version: int,
    file: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    error_msg = ""
    required_options_provided = True

    if not name:
        required_options_provided = False
        error_msg += "\nName of the brain is required"

    if not file:
        required_options_provided = False
        error_msg += "\nPath to inkling file is required"

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    if not version:
        version = get_latest_brain_version(name, "Update-inkling brain version", debug, output, test)

    try:
        get_brain_version_response = api(use_aad=True).get_brain_version(
            name, version, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Update-inkling brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if get_brain_version_response["state"] == "Active":
        raise_as_click_exception("Cannot update inkling when training is active")

    if get_brain_version_response["assessmentState"] == "Active":
        raise_as_click_exception("Cannot update inkling when assessment is active")

    try:
        f = open(file, "r")
        inkling = f.read()
        f.close()

    except FileNotFoundError as e:
        raise_as_click_exception(e)

    try:
        response = api(use_aad=True).update_brain_version_inkling(
            name,
            version=version,
            inkling=inkling,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "Uploaded {} to {} version {}.".format(
        file, name, response["version"]
    )

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


@click.command("get-inkling", short_help="Get inkling of a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to get inkling, defaults to latest.")
@click.option("--file", "-f", help="File to write inkling.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def get_inkling(
    ctx: click.Context,
    name: str,
    version: int,
    file: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(name, "Get-inkling brain version", debug, output, test)

    try:
        response = api(use_aad=True).get_brain_version(
            name, version, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception['statusCode'] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Get-inkling brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if len(response["inkling"]) == 0:
        raise_as_click_exception("Inkling is not set")

    if file:
        f = open(file, "w+")
        f.write(response["inkling"])
        f.close()

        status_message = "Inkling saved from {} version {} to {}.".format(
            name, response["version"], file
        )
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
    else:
        if output == "json":
            json_response = {
                "status": response["status"],
                "statusCode": response["statusCode"],
                "inkling": response["inkling"],
            }

            if test:
                json_response["elapsed"] = str(response["elapsed"])
                json_response["timeTaken"] = str(response["timeTaken"])

            click.echo(dumps(json_response, indent=4))

        else:
            click.echo(response["inkling"])

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("start-training", short_help="Start training a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to start training, defaults to latest.")
@click.option(
    "--simulator-package-name",
    help="Simulator package to use for training in the case of managed simulators.",
)
@click.option("--concept-name", "-c", help="Concept to train.")
@click.option(
    "--instance-count", "-i",type=int, help="Number of instances to perform training with."
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def start_training(
    ctx: click.Context,
    name: str,
    version: int,
    simulator_package_name: str,
    concept_name: str,
    instance_count: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(name, "Start-training brain version", debug, output, test)

    if not concept_name:
        try:
            show_brain_version_response = api(use_aad=True).get_brain_version(
                name, version, workspace=workspace_id, debug=debug, output=output
            )
        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        if len(show_brain_version_response["concepts"]) > 0:
            concept_name = show_brain_version_response["concepts"][0]["name"]

        else:
            raise_as_click_exception(
                "Concept name not provided and no concept name found in inkling"
            )

    if simulator_package_name:
        try:
            show_simulator_package_response = api(use_aad=True).get_sim_package(
                simulator_package_name,
                workspace=workspace_id,
                debug=debug,
                output=output,
            )
        except BrainServerError as e:
            if e.exception['statusCode'] == 404:
                raise_not_found_as_click_exception(
                    debug,
                    output,
                    "Starting managed simulator",
                    "Simulator package",
                    simulator_package_name,
                    test,
                    e,
                )
            else:
                raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        cores_per_instance = show_simulator_package_response["coresPerInstance"]
        memory_in_gb_per_instance = show_simulator_package_response[
            "memInGbPerInstance"
        ]
        min_instance_count = show_simulator_package_response["minInstanceCount"]
        max_instance_count = show_simulator_package_response["maxInstanceCount"]
        auto_scaling = show_simulator_package_response["autoScale"]
        auto_termination = show_simulator_package_response["autoTerminate"]

        if not instance_count:
            instance_count = show_simulator_package_response["startInstanceCount"]

        try:
            api(use_aad=True).create_sim_collection(
                packagename=simulator_package_name,
                brain_name=name,
                brain_version=version,
                purpose_action="Train",
                concept_name=concept_name,
                description="desc",
                cores_per_instance=cores_per_instance,
                memory_in_gb_per_instance=memory_in_gb_per_instance,
                start_instance_count=instance_count,
                min_instance_count=min_instance_count,
                max_instance_count=max_instance_count,
                auto_scaling=auto_scaling,
                auto_termination=auto_termination,
                workspace=workspace_id,
                debug=debug,
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    try:
        response = api(use_aad=True).start_training(
            name, version=version, workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        if e.exception['statusCode'] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Start-training brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "{} version {} training started.".format(name, version)

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("stop-training", short_help="Stop training a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to stop training, defaults to latest.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def stop_training(
    ctx: click.Context,
    name: str,
    version: int,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(name, "Stop-training brain version", debug, output, test)

    try:
        response = api(use_aad=True).stop_training(
            name, version=version, workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        if e.exception['statusCode'] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Stop-training brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "{} version {} training stopped.".format(
        name, response["version"]
    )

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("reset-training", short_help="Reset training for a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--concept-name", "-c", help="[Required] Name of the concept to reset.")
@click.option("--lesson-number", "-e", type=int, help="[Required] Lesson number to reset.")
@click.option("--version", type=int, help="Version to reset training, defaults to latest.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def reset_training(
    ctx: click.Context,
    name: str,
    version: int,
    concept_name: str,
    lesson_number: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    error_msg = ""
    required_options_provided = True

    if not name:
        required_options_provided = False
        error_msg += "\nName of the brain is required"

    if not concept_name:
        required_options_provided = False
        error_msg += "\nConcept name is required"

    if not lesson_number:
        required_options_provided = False
        error_msg += "\nLesson number is required"

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    if not version:
        version = get_latest_brain_version(name, "Reset-training brain version", debug, output, test)

    try:
        log.debug("Resetting training for BRAIN: {}".format(id))
        response = api(use_aad=True).reset_training(
            name,
            version=version,
            concept_name=concept_name,
            lesson_number=lesson_number,
            workspace=workspace_id,
            debug=debug,
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "{} version {} training reset.".format(
        name, response["version"]
    )

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("start-assessing", short_help="Start assessing a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to start assessing, defaults to latest.")
@click.option(
    "--simulator-package-name",
    help="Simulator package to use for assessing in the case of managed simulators.",
)
@click.option("--concept-name", "-c", help="Concept to assess.")
@click.option(
    "--instance-count", "-i",type=int, help="Number of instances to perform assessing with."
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def start_assessing(
    ctx: click.Context,
    name: str,
    version: int,
    simulator_package_name: str,
    concept_name: str,
    instance_count: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(name, "Start-assessing brain version", debug, output, test)

    if not concept_name:
        try:
            show_brain_version_response = api(use_aad=True).get_brain_version(
                name, version, workspace=workspace_id, debug=debug, output=output
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        if len(show_brain_version_response["concepts"]) > 0:
            concept_name = show_brain_version_response["concepts"][0]["name"]

        else:
            raise_as_click_exception(
                "Concept name not provided and no concept name found in inkling"
            )

    try:
        response = api(use_aad=True).start_assessment(
            name, version=version, workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        if e.exception['statusCode'] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Start-assessing brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if simulator_package_name:
        try:
            show_simulator_package_response = api(use_aad=True).get_sim_package(
                simulator_package_name,
                workspace=workspace_id,
                debug=debug,
                output=output,
            )
        except BrainServerError as e:
            if e.exception['statusCode'] == 404:
                raise_not_found_as_click_exception(
                    debug,
                    output,
                    "Starting managed simulator",
                    "Simulator package",
                    simulator_package_name,
                    test,
                    e,
                )
            else:
                raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        cores_per_instance = show_simulator_package_response["coresPerInstance"]
        memory_in_gb_per_instance = show_simulator_package_response[
            "memInGbPerInstance"
        ]
        min_instance_count = show_simulator_package_response["minInstanceCount"]
        max_instance_count = show_simulator_package_response["maxInstanceCount"]
        auto_scaling = show_simulator_package_response["autoScale"]
        auto_termination = show_simulator_package_response["autoTerminate"]

        if not instance_count:
            instance_count = show_simulator_package_response["startInstanceCount"]

        try:
            api(use_aad=True).create_sim_collection(
                packagename=simulator_package_name,
                brain_name=name,
                brain_version=version,
                purpose_action="Assess",
                concept_name=concept_name,
                description="desc",
                cores_per_instance=cores_per_instance,
                memory_in_gb_per_instance=memory_in_gb_per_instance,
                start_instance_count=instance_count,
                min_instance_count=min_instance_count,
                max_instance_count=max_instance_count,
                auto_scaling=auto_scaling,
                auto_termination=auto_termination,
                workspace=workspace_id,
                debug=debug,
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    status_message = "{} version {} assessing started.".format(name, version)

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("stop-assessing", short_help="Stop assessing a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to stop assessing, defaults to latest.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def stop_assessing(
    ctx: click.Context,
    name: str,
    version: int,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(name, "Stop-assessing brain version", debug, output, test)

    try:
        response = api(use_aad=True).stop_assessment(
            name, version=version, workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        if e.exception['statusCode'] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Stop-assessing brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "{} version {} assessing stopped.".format(
        name, response["version"]
    )

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


def get_latest_brain_version(name: str,
                             operation: str,
                             debug: bool,
                             output: str,
                             test: bool):
    try:
        response = api(use_aad=True).list_brain_versions(name)

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                operation,
                "Brain",
                name,
                test,
                e,
            )

        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    brain_versions_desc = sorted(
        response["value"], key=lambda i: i["version"], reverse=True
    )

    return brain_versions_desc[0]["version"]


@click.group()
def simulator():
    """Simulator operations."""
    pass


@click.group()
def package():
    """Simulator package operations."""
    pass


@click.command("add", short_help="Add a simulator package.")
@click.option(
    "--name", "-n", help="[Required] Name of the simulator package."
)
@click.option(
    "--image-uri", "-u", help="[Required] URI of the simulator package (container)."
)
@click.option(
    "--instance-count",
    "-i",type=int,
    help="[Required] Number of instances to perform training with the simulator package.",
)
@click.option(
    "--cores-per-instance",
    "-r",type=float,
    help="[Required] Number of cores that should be allocated for each simulator instance.",
)
@click.option(
    "--memory-in-gb-per-instance",
    "-m", type=float,
    help="[Required] Memory in GB that should be allocated for each simulator instance.",
)
@click.option(
    "--os-type",
    "-p",
    help="[Required] OS type for the simulator package. Windows or Linux.",
)
@click.option("--display-name", help="Display name of the simulator package.")
@click.option("--description", help="Description for the simulator package.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def add_simulator_package(
    ctx: click.Context,
    name: str,
    image_uri: str,
    instance_count: int,
    cores_per_instance: float,
    memory_in_gb_per_instance: float,
    os_type: str,
    display_name: str,
    description: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    error_msg = ""
    required_options_provided = True

    if not name:
        required_options_provided = False
        error_msg += "\nName of the simulator package is required"

    if not instance_count:
        required_options_provided = False
        error_msg += "\nInstance count of the simulator is required"

    if not image_uri:
        required_options_provided = False
        error_msg += "\nUri for the simulator package is required"

    if not cores_per_instance:
        required_options_provided = False
        error_msg += "\nCores per instance for the simulator is required"

    if not memory_in_gb_per_instance:
        required_options_provided = False
        error_msg += "\nMemory in GB per instance for the simulator is required"

    if not os_type:
        required_options_provided = False
        error_msg += "\nOS type for the simulator package is required"

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    try:
        response = api(use_aad=True).create_sim_package(
            name=name,
            image_path=image_uri,
            start_instance_count=instance_count,
            cores_per_instance=cores_per_instance,
            memory_in_gb_per_instance=memory_in_gb_per_instance,
            display_name=display_name,
            description=description,
            os_type=os_type,
            package_type="container",
            min_instance_count=instance_count,
            max_instance_count=instance_count,
            auto_scale=False,
            auto_terminate=True,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

    except BrainServerError as e:
        if "Unique index constraint violation" in str(e):
            raise_unique_constraint_violation_as_click_exception(
                debug, output, "Simulator package", name, test, e
            )
        else:
            raise_as_click_exception(e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "Created new simulator package {}.".format(response["name"])

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about a simulator package.")
@click.option(
    "--name",
    "-n",
    help="[Required] The name of the simulator package to show.",
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def show_simulator_package(
    ctx: click.Context,
    name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the simulator package is required")

    try:
        response = api(use_aad=True).get_sim_package(
            name, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Show simulator package",
                "Simulator package",
                name,
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)
    except AuthenticationError as e:
        raise_as_click_exception(e)

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": {
                "Name": response["name"],
                "acrUri": response["imagePath"],
                "cores": response["coresPerInstance"],
                "memory": response["memInGbPerInstance"],
                "instanceCount": response["startInstanceCount"],
            },
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo("Name: {}".format(response["name"]))
        click.echo("ACR URI: {}".format(response["imagePath"]))
        click.echo("CORES (in vCPU): {}".format(response["coresPerInstance"]))
        click.echo("MEMORY (in GB): {}".format(response["memInGbPerInstance"]))
        click.echo("INSTANCE COUNT: {}".format(response["startInstanceCount"]))

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("update", short_help="Update information about a simulator package.")
@click.option(
    "--name", "-n", help="[Required] Name of the simulator package."
)
@click.option(
    "--instance-count",
    "-i",type=int,
    help="Number of instances to perform training with the simulator package.",
)
@click.option(
    "--cores-per-instance",
    "-r",type=float,
    help="Number of cores that should be allocated for each simulator instance.",
)
@click.option(
    "--memory-in-gb-per-instance",
    "-m", type=float,
    help="Memory in GB that should be allocated for each simulator instance.",
)
@click.option("--display-name", help="Display name of the simulator package.")
@click.option("--description", help="Description for the simulator package.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def update_simulator_package(
    ctx: click.Context,
    name: str,
    instance_count: int,
    cores_per_instance: float,
    memory_in_gb_per_instance: float,
    display_name: str,
    description: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the simulator package is required")

    try:
        response = api(use_aad=True).update_sim_package(
            name=name,
            start_instance_count=instance_count,
            cores_per_instance=cores_per_instance,
            memory_in_gb_per_instance=memory_in_gb_per_instance,
            display_name=display_name,
            description=description,
            min_instance_count=instance_count,
            max_instance_count=instance_count,
            auto_scale=False,
            auto_terminate=True,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Update simulator package",
                "Simulator package",
                name,
                test,
                e,
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


@click.command("list", short_help="Lists simulator packages owned by current user.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def list_simulator_package(
    ctx: click.Context, workspace_id: str, debug: bool, output: str, test: bool
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_sim_package(
            workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if len(response["value"]) == 0:
        click.echo("No simulator packages exist for the current user")
        ctx.exit()

    if output == "json":
        dict_rows = []
        for simulator_package in response["value"]:
            dict_rows.append(simulator_package["name"])

        json_response = {
            "value": dict_rows,
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": "",
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        for simulator_package in response["value"]:
            click.echo(simulator_package["name"])

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("remove", short_help="Remove a simulator package.")
@click.option(
    "--name",
    "-n",
    help="[Required] The name of the simulator package to remove.",
)
@click.option(
    "--yes", "-y", default=False, is_flag=True, help="Do not prompt for confirmation."
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
)
@click.option(
    "--debug",
    default=False,
    is_flag=True,
    help="Increase logging verbosity to show all logs.",
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
def remove_simulator_package(
    ctx: click.Context,
    name: str,
    yes: bool,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=True)

    if not name:
        raise_as_click_exception("\nName of the simulator package is required")

    is_delete = True

    if not yes:
        click.echo(
            "Are you sure you want to remove simulator package {} (y/n?).".format(
                name
            )
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
            response = api(use_aad=True).delete_sim_package(
                name, workspace=workspace_id, debug=debug
            )

            if response["statusCode"] ==204:
                raise_client_side_click_exception(debug, output, test, 204, "Simulator package '{}' not found".format(name), response)

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        status_message = "{} removed. NOTE: Removing {} will not remove the container image of the simulator in ACR.".format(
            name, name
        )

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


@click.group()
def unmanaged():
    """Unmanaged simulator operations."""
    pass


@click.command("list", short_help="Lists unmanaged simulators owned by current user.")
@click.option("--simulator-name", help="Filter by simulator name.")
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def list_simulator_unmanaged(
    ctx: click.Context,
    simulator_name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_unmanaged_sim_session(
            workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    rows = []
    dict_rows = []
    if simulator_name:
        for item in response["value"]:
            try:
                if item["simulatorName"] == simulator_name:
                    name = item["simulatorName"]
                    session_id = item["sessionId"]
                    if (
                        item["simulatorContext"]["purpose"]["action"] == "Train"
                        or item["simulatorContext"]["purpose"]["action"] == "Assess"
                    ):
                        action = item["simulatorContext"]["purpose"]["action"]
                    else:
                        action = "Unset"

                    rows.append([name, session_id, action])
                    dict_rows.append(
                        {"name": name, "sessionId": session_id, "action": action}
                    )
            except KeyError:
                pass  # If it's missing a field, ignore it.

        if len(rows) == 0:
            click.echo(
                "No unmanaged simulators with simulator name {} exist for the current user".format(
                    simulator_name
                )
            )
            ctx.exit()

    else:
        for item in response["value"]:
            try:
                name = item["simulatorName"]
                session_id = item["sessionId"]
                if (
                    item["simulatorContext"]["purpose"]["action"] == "Train"
                    or item["simulatorContext"]["purpose"]["action"] == "Assess"
                ):
                    action = item["simulatorContext"]["purpose"]["action"]
                else:
                    action = "Unset"

                rows.append([name, session_id, action])
                dict_rows.append(
                    {"name": name, "sessionId": session_id, "action": action}
                )
            except KeyError:
                pass  # If it's missing a field, ignore it.

            if len(rows) == 0:
                click.echo("No unmanaged simulators exist for the current user")
                ctx.exit()

    if output == "json":
        json_response = {
            "value": dict_rows,
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": "",
        }

        click.echo(dumps(json_response, indent=4))

    else:
        table = tabulate(
            rows, headers=["NAME", "SESSION-ID", "ACTION"], tablefmt="orgtbl"
        )
        click.echo(table)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about an unmanaged simulator.")
@click.option(
    "--session-id", "-d", help="[Required] Identifier for the unmanaged simulator."
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def show_simulator_unmanaged(
    ctx: click.Context,
    session_id: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    if not session_id:
        raise_as_click_exception("\nIdentifier for the unmanaged simulator is required")

    try:
        response = api(use_aad=True).get_sim_session(
            session_id, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception['statusCode'] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Show simulator unmanaged",
                "Simulator unmanaged",
                session_id,
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if (
        response["simulatorContext"]["purpose"]["action"] == "Train"
        or response["simulatorContext"]["purpose"]["action"] == "Assess"
    ):
        action = response["simulatorContext"]["purpose"]["action"]
    else:
        action = "Unset"

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": {"Name": response["interface"]["name"], "action": action},
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo("Name: {}".format(response["interface"]["name"]))
        click.echo("Action: {}".format(action))

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("connect", short_help="Connect an unmanaged simulator.")
@click.option(
    "--brain-name",
    "-b",
    help="[Required] The name of the brain for the simulators to connect to.",
)
@click.option(
    "--action", "-a", help="[Required] The assigned action for the simulators."
)
@click.option(
    "--concept-name",
    "-c",
    help="[Required] The name of the concept for the simulators to connect to.",
)
@click.option(
    "--brain-version", type=int,
    help="The version of the brain for the simulators to connect to, defaults to latest.",
)
@click.option("--session-id", "-d", help="Identifier for the simulator.")
@click.option(
    "--simulator-name",
    help="The name of the simulator, provide this if you would like to connect all simulators with this name.",
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
def connect_simulator_unmanaged(
    ctx: click.Context,
    session_id: str,
    brain_name: str,
    brain_version: int,
    action: str,
    concept_name: str,
    simulator_name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = _get_version_checker(ctx, interactive=not output)

    error_msg = ""
    required_options_provided = True

    if not brain_name:
        required_options_provided = False
        error_msg += "\nBrain name is required"

    if not action:
        required_options_provided = False
        error_msg += "\nAction is required"

    if not concept_name:
        required_options_provided = False
        error_msg += "\nConcept name is required"

    if session_id and simulator_name:
        required_options_provided = False
        error_msg += "\nPlease provide either session id or simulator name but not both"

    if not session_id and not simulator_name:
        required_options_provided = False
        error_msg += "\nPlease provide either session id or simulator name"

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    if not brain_version:
        brain_version = get_latest_brain_version(brain_name, "Connect simulator unmanaged", debug, output, test)

    action = action.capitalize()

    if simulator_name:
        try:
            response = api(use_aad=True).list_unmanaged_sim_session(
                workspace=workspace_id, debug=False, output=output
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        total_simulators = 0

        inactive_simulators = 0
        active = 0
        failure_status_code = 500

        for sim in response["value"]:
            if sim["simulatorName"] == simulator_name:
                total_simulators += 1

                if (
                    sim["simulatorContext"]["purpose"]["action"] == "Train"
                    or sim["simulatorContext"]["purpose"]["action"] == "Assess"
                ):
                    active += 1

                if sim["simulatorContext"]["purpose"]["action"] == "Inactive":
                    try:
                        api(use_aad=True).patch_sim_session(
                            session_id=sim["sessionId"],
                            brain_name=brain_name,
                            version=brain_version,
                            purpose_action=action,
                            concept_name=concept_name,
                            workspace=workspace_id,
                            debug=debug,
                            output=output,
                        )

                        active += 1

                    except BrainServerError as e:
                        if inactive_simulators == 0:
                            failure_status_code: int = e.exception["statusCode"]
                        inactive_simulators += 1

        if output == "json":
            status_message = {
                "simulatorsFound": total_simulators,
                "simulatorsConnected": active,
                "simulatorsNotConnected": inactive_simulators,
            }

            if inactive_simulators > 0:
                json_response = {
                    "status": "Failed",
                    "statusCode": failure_status_code,
                    "statusMessage": status_message,
                }
            else:
                json_response = {
                    "status": "Succeeded",
                    "statusCode": 200,
                    "statusMessage": status_message,
                }

            click.echo(dumps(json_response, indent=4))
        else:
            click.echo("Simulators Found: {}".format(total_simulators))
            click.echo("Simulators Connected: {}".format(active))
            click.echo("Simulators Not Connected: {}".format(inactive_simulators))

    else:
        try:
            show_sim_session_response = api(use_aad=True).get_sim_session(
                session_id=session_id,
                workspace=workspace_id,
                debug=debug,
                output=output,
            )

        except BrainServerError as e:
            if e.exception['statusCode'] == 404:
                raise_not_found_as_click_exception(
                    debug,
                    output,
                    "Connect simulator unmanaged",
                    "Simulator unmanaged",
                    session_id,
                    test,
                    e,
                )
            else:
                raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        if (
            show_sim_session_response["simulatorContext"]["purpose"]["action"]
            == "Train"
            or show_sim_session_response["simulatorContext"]["purpose"]["action"]
            == "Assess"
        ):
            raise_as_click_exception(
                "Unmanaged simulator with session id {} is already connected to brain {} version {} with action {}".format(
                    session_id,
                    show_sim_session_response["simulatorContext"]["purpose"]["target"][
                        "brainName"
                    ],
                    show_sim_session_response["simulatorContext"]["purpose"]["target"][
                        "brainVersion"
                    ],
                    show_sim_session_response["simulatorContext"]["purpose"]["action"],
                )
            )

        try:
            response = api(use_aad=True).patch_sim_session(
                session_id=session_id,
                brain_name=brain_name,
                version=brain_version,
                purpose_action=action,
                concept_name=concept_name,
                workspace=workspace_id,
                debug=debug,
                output=output,
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        status_message = "{} set to {} on brain {} version {}. ".format(
            session_id, action, brain_name, brain_version
        )

        if output == "json":
            json_response = {
                "status": response["status"],
                "statusCode": response["statusCode"],
                "statusMessage": status_message,
            }

            click.echo(dumps(json_response, indent=4))

        else:
            click.echo(status_message)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


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
    help="[Required] Processor architecture for the exported brain.",
)
@click.option(
    "--brain-name", "-bn", help="[Required] Name of the brain to be exported."
)
@click.option(
    "--brain-version", "-bv", help="[Required] Version of the brain to be exported"
)
@click.option(
    "--workspace-id",
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
):
    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the exported brain is required")

    if not processor_architecture:
        raise_as_click_exception("Processor architecture is required")

    if not name:
        raise_as_click_exception("Name of the brain to be exported is required")

    if not brain_version:
        raise_as_click_exception("Version of the brain to be exported is required")

    try:
        response = api(use_aad=True).create_exported_brain(
            name,
            display_name=display_name,
            description=description,
            processor_architecture=processor_architecture,
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
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
    version_checker = _get_version_checker(ctx, interactive=not output)

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
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
    version_checker = _get_version_checker(ctx, interactive=not output)

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
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
    version_checker = _get_version_checker(ctx, interactive=not output)

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
    "-wid",
    help="Please provide the workspace id if you would like to override the default target workspace.",
    hidden=True,
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
    version_checker = _get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the exported brain is required")

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


@click.command()
@click.option("--workspace-id", "-w", help="[Required] Workspace ID.")
@click.option("--tenant-id", help="Tenant ID.")
@click.option("--show", is_flag=True, help="Prints active profile information.")
@click.pass_context
def configure(
    ctx: click.Context,
    workspace_id: str,
    tenant_id: Optional[str] = None,
    show: bool = False,
):
    """Authenticate with the Server."""
    version_checker = _get_version_checker(ctx, interactive=True)

    if not workspace_id:
        raise_as_click_exception("Workspace ID is required")

    bonsai_config = Config(use_aad=True, require_workspace=False)

    args = {
        "workspace_id": workspace_id,
        "tenant_id": tenant_id,
        "url": "https://cp-api.bons.ai",
        "gateway_url": "https://api.bons.ai",
    }

    bonsai_config.update(**args)

    if show:
        print_profile_information(bonsai_config)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("switch", short_help="Switch profile.", hidden=True)
@click.argument("profile", required=False)
@click.option("--workspace-id", "-wid", help="Workspace ID.")
@click.option("--tenant-id", "-tid", help="Tenant ID.")
@click.option("--url", "-u", default=None, help="Set the brain api url.")
@click.option("--gateway-url", "-g", default=None, help="Set the brain gateway url.")
@click.option("--show", "-s", is_flag=True, help="Prints active profile information")
@click.pass_context
def switch(
    ctx: click.Context,
    profile: str,
    workspace_id: Optional[str],
    tenant_id: Optional[str],
    url: Optional[str],
    gateway_url: Optional[str],
    show: bool,
):
    """
    Change the active configuration section.\n
    For new profiles you must provide a url with the --url option.
    """
    version_checker = _get_version_checker(ctx, interactive=True)

    config = Config(argv=sys.argv, use_aad=False)
    # `bonsai switch` and `bonsai switch -h/--help have the same output
    if not profile and not show:
        help_message: str = ctx.get_help()
        click.echo(message=help_message)
        list_profiles(config)
        ctx.exit(0)

    if not profile and show:
        print_profile_information(config)
        ctx.exit(0)

    # Let the user know that when switching to a new profile
    # the --workspace-id, --tenant-id, --url and --gateway_url options must be provided
    section_exists = config.has_section(profile)
    if not section_exists:
        error_msg = "\nProfile not found."
        required_options_provided = True

        if not workspace_id:
            required_options_provided = False
            error_msg += "\nPlease provide a workspace id with the --workspace-id option for new profiles"

        if not url:
            required_options_provided = False
            error_msg += "\nPlease provide a url with the --url option for new profiles"

        if not gateway_url:
            required_options_provided = False
            error_msg += "\nPlease provide a gateway url with the --gateway-url option for new profiles"

        if not required_options_provided:
            click.echo(error_msg)
            ctx.exit(1)

    config.update(profile=profile)

    if workspace_id:
        config.update(workspace_id=workspace_id)

    if tenant_id:
        config.update(tenant_id=tenant_id)

    if url:
        config.update(url=url)

    if gateway_url:
        config.update(gateway_url=gateway_url)

    if show:
        print_profile_information(config)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--version",
    "-v",
    is_flag=True,
    callback=_version_callback,
    help="Show the version and check if Bonsai is up to date.",
    expose_value=False,
    is_eager=True,
)
@click.option(
    "--sysinfo",
    "-s",
    is_flag=True,
    callback=_sysinfo,
    help="Show system information.",
    expose_value=False,
    is_eager=True,
)
@click.option("--timeout", "-t", type=int, help="Set timeout for CLI API requests.")
@click.option(
    "--enable-color/--disable-color",
    callback=_set_color,
    help="Enable/disable color printing.",
    expose_value=False,
    is_eager=True,
    default=None,
)
@click.option(
    "--disable-version-check",
    "-dv",
    is_flag=True,
    default=False,
    help="Flag to disable version checking when running commands.",
)
@click.pass_context
def cli(ctx: click.Context, timeout: int, disable_version_check: bool):
    """Command line interface for the Microsoft Bonsai Service.
    """
    if timeout:
        BonsaiAPI.TIMEOUT = timeout

    ctx.ensure_object(dict)
    ctx.obj["VERSION_CHECK"] = False if disable_version_check else True


@click.command("help")
@click.pass_context
def bonsai_help(ctx: click.Context):
    """ Show this message and exit. """
    version_checker = _get_version_checker(ctx, interactive=True)
    assert ctx.parent is not None
    click.echo(ctx.parent.get_help())
    version_checker.check_cli_version(wait=True, print_up_to_date=False)


cli.add_command(bonsai_help)

cli.add_command(brain)
cli.add_command(exportedbrain)
cli.add_command(simulator)
cli.add_command(switch)
cli.add_command(configure)

brain.add_command(create_brain)
brain.add_command(show_brain)
brain.add_command(update_brain)
brain.add_command(list_brain)
brain.add_command(delete_brain)

brain.add_command(version)

version.add_command(create_brain_version)
version.add_command(show_brain_version)
version.add_command(update_brain_version)
version.add_command(list_brain_version)
version.add_command(delete_brain_version)
version.add_command(update_inkling)
version.add_command(get_inkling)
version.add_command(start_training)
version.add_command(stop_training)
version.add_command(reset_training)

version.add_command(start_assessing)
version.add_command(stop_assessing)

simulator.add_command(package)

package.add_command(add_simulator_package)
package.add_command(show_simulator_package)
package.add_command(update_simulator_package)
package.add_command(list_simulator_package)
package.add_command(remove_simulator_package)

simulator.add_command(unmanaged)

unmanaged.add_command(connect_simulator_unmanaged)
unmanaged.add_command(list_simulator_unmanaged)
unmanaged.add_command(show_simulator_unmanaged)

exportedbrain.add_command(create_exportedbrain)
exportedbrain.add_command(show_exportedbrain)
exportedbrain.add_command(update_exportedbrain)
exportedbrain.add_command(list_exportedbrain)
exportedbrain.add_command(delete_exportedbrain)


def main():
    cli()


if __name__ == "__main__":
    raise RuntimeError("run ../bonsai.py instead.")
