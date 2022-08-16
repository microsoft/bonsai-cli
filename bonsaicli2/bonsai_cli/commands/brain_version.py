"""
This file contains the code for commands that target a bonsai brain version in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

from typing import Any, Dict, List, Optional
import click
import os
import shutil
from datetime import datetime
from json import dumps
from tabulate import tabulate

from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    get_latest_brain_version,
    get_version_checker,
    raise_204_click_exception,
    raise_as_click_exception,
    raise_client_side_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_not_found_as_click_exception,
)

from bonsai_cli.commands.diaglets.diaglet_base import Diaglet

from .assessment import assessment


@click.group("version", short_help="Brain version operations.")
def version():
    """
    brain version operations.
    """
    pass


@click.command("copy", short_help="Clone a brain version from an existing version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version",
    type=int,
    help="Provide the version of the brain to be copied, defaults to latest.",
)
@click.option("--notes", help="Notes to be added to the brain version.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
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

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Copy brain version", debug, output, test
        )

    try:
        response = api(use_aad=True).create_brain_version(
            name,
            version,
            description=notes,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

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

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Copy brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to show, defaults to latest.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
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

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Show brain version", debug, output, test
        )

    try:
        response = api(use_aad=True).get_brain_version(
            name, version, workspace=workspace_id, debug=debug, output=output
        )

        if output == "json":
            json_response = {
                "version": response["version"],
                "trainingState": response["state"],
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
            click.echo("Notes: {}".format(response["description"]))
            click.echo("Created On: {}".format(response["createdOn"]))
            click.echo("Modified On: {}".format(response["modifiedOn"]))

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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("update", short_help="Update information about a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to update, defaults to latest.")
@click.option("--notes", help="Notes to be added to the brain version.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
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

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Update brain version", debug, output, test
        )

    try:
        response = api(use_aad=True).update_brain_version_details(
            name,
            version=version,
            description=notes,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("list", short_help="List versions of a brain.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
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

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    try:
        response = api(use_aad=True).list_brain_versions(
            name, workspace=workspace_id, debug=debug, output=output
        )

        rows: List[Any] = []
        dict_rows: List[Dict[str, Any]] = []
        for item in response["value"]:
            try:
                version = item["version"]
                training_state = item["state"]
                rows.append([version, training_state])
                dict_rows.append({"version": version, "trainingState": training_state})
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
                headers=["Version", "Training State"],
                tablefmt="orgtbl",
            )
            click.echo(table)

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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("delete", short_help="Delete a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to delete, defaults to latest.")
@click.option(
    "--yes", "-y", default=False, is_flag=True, help="Do not prompt for confirmation."
)
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
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

    version_checker = get_version_checker(ctx, interactive=True)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Delete brain version", debug, output, test
        )

    is_delete = False

    if yes:
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
        try:
            response = api(use_aad=True).delete_brain_version(
                name, version=version, workspace=workspace_id, debug=debug
            )

            if response["statusCode"] == 204:
                raise_204_click_exception(
                    debug,
                    output,
                    test,
                    204,
                    "Brain '{}' version '{}' not found".format(name, version),
                    response,
                )

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

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("update-inkling", short_help="Update inkling of a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--file", "-f", help="[Required] Path to inkling file.")
@click.option(
    "--version", type=int, help="Version to update inkling, defaults to latest."
)
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
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

    version_checker = get_version_checker(ctx, interactive=not output)

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
        version = get_latest_brain_version(
            name, "Update-inkling brain version", debug, output, test
        )

    try:
        get_brain_version_response = api(use_aad=True).get_brain_version(
            name, version, workspace=workspace_id, debug=debug, output=output
        )

        if get_brain_version_response["state"] == "Active":
            raise_as_click_exception("Cannot update inkling when training is active")

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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

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

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("get-inkling", short_help="Get inkling of a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option("--version", type=int, help="Version to get inkling, defaults to latest.")
@click.option("--file", "-f", help="File to write inkling.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
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

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Get-inkling brain version", debug, output, test
        )

    try:
        response = api(use_aad=True).get_brain_version(
            name, version, workspace=workspace_id, debug=debug, output=output
        )

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

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("start-training", short_help="Start training a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version", type=int, help="Version to start training, defaults to latest."
)
@click.option(
    "--simulator-package-name",
    help="Simulator package to use for training in the case of managed simulators.",
)
@click.option("--concept-name", "-c", help="Concept to train.")
@click.option(
    "--instance-count",
    "-i",
    type=int,
    help="Number of instances to perform training with, in the case of managed simulators.",
)
@click.option(
    "--log-session-count",
    "-s",
    default=1,
    type=int,
    help="Number of simulators to enable training logging for, in the case of managed simulators. Default is 1.",
)
@click.option(
    "--include-system-logs",
    "-l",
    default=False,
    is_flag=True,
    help="Including system logs will collect additional logs from your managed simulators for which logging is enabled for, in the case of managed simulators.",
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
def start_training(
    ctx: click.Context,
    name: str,
    version: int,
    simulator_package_name: str,
    concept_name: str,
    instance_count: str,
    log_session_count: str,
    include_system_logs: bool,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Start-training brain version", debug, output, test
        )

    if not concept_name:
        try:
            show_brain_version_response = api(use_aad=True).get_brain_version(
                name, version, workspace=workspace_id, debug=debug, output=output
            )

            if len(show_brain_version_response["concepts"]) > 0:
                concept_name = show_brain_version_response["concepts"][0]["name"]

            else:
                raise_as_click_exception(
                    "Concept name not provided and no concept name found in inkling"
                )

        except BrainServerError as e:
            if e.exception["statusCode"] == 404:
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

        except Exception as e:
            raise_client_side_click_exception(
                output, test, "{}: {}".format(type(e), e.args)
            )

    if instance_count and not simulator_package_name:
        raise_as_click_exception(
            "\nInstance count works only with a simulator package, please provide the name of the simulator package you would like to use"
        )

    if int(log_session_count) != 1 and not simulator_package_name:
        raise_as_click_exception(
            "\nLog session count works only with a simulator package, please provide the name of the simulator package you would like to use"
        )

    if include_system_logs and not simulator_package_name:
        raise_as_click_exception(
            "\nIncluding system logs works only with a simulator package, please provide the name of the simulator package you would like to use"
        )

    if simulator_package_name:
        try:
            show_simulator_package_response = api(use_aad=True).get_sim_package(
                simulator_package_name,
                workspace=workspace_id,
                debug=debug,
                output=output,
            )

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

        except BrainServerError as e:
            if e.exception["statusCode"] == 404:
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

        except Exception as e:
            raise_client_side_click_exception(
                output, test, "{}: {}".format(type(e), e.args)
            )

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
                log_session_count=log_session_count,
                include_system_logs=include_system_logs,
                log_all_simulators=False,
                workspace=workspace_id,
                debug=debug,
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        except Exception as e:
            raise_client_side_click_exception(
                output, test, "{}: {}".format(type(e), e.args)
            )

    try:
        concept_names: Optional[List[str]] = [concept_name] if concept_name else None

        response = api(use_aad=True).start_training(
            name,
            version=version,
            workspace=workspace_id,
            debug=debug,
            concept_names=concept_names,
        )

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

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("stop-training", short_help="Stop training a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version", type=int, help="Version to stop training, defaults to latest."
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
def stop_training(
    ctx: click.Context,
    name: str,
    version: int,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Stop-training brain version", debug, output, test
        )

    try:
        response = api(use_aad=True).stop_training(
            name, version=version, workspace=workspace_id, debug=debug
        )

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

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command(
    "start-logging",
    short_help="Start logging for a simulator session.",
)
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version", type=int, help="Version to start logging, defaults to latest."
)
@click.option(
    "--workspace-id",
    "-w",
    type=str,
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--managed-simulator",
    "-m",
    type=str,
    default=False,
    is_flag=True,
    help="Please use this flag if this is for managed simulators.",
)
@click.option(
    "--all",
    default=False,
    is_flag=True,
    hidden=True,
    help="Flag to log iterations for all managed simulators. This cannot be set at the same with --log-session-count.",
)
@click.option(
    "--session-id",
    "-d",
    type=str,
    help="Identifier for the simulator, in the case of unmanaged simulators.",
)
@click.option(
    "--log-session-count",
    "-s",
    type=int,
    default=4,
    help="Number of simulators to enable iterations logging for, in the case of managed simulators. Default is 4. This cannot be set at the same with --all.",
)
@click.option(
    "--include-system-logs",
    "-l",
    default=False,
    is_flag=True,
    help="Including system logs will collect additional logs from your managed simulators. Please note that this will cause some or all of your managed simulators to restart, in the case of managed simulators.",
)
@click.option(
    "--yes",
    "-y",
    default=False,
    is_flag=True,
    help="Do not prompt for confirmation when including system logs.",
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
def start_logging(
    ctx: click.Context,
    name: str,
    version: int,
    workspace_id: str,
    managed_simulator: bool,
    all: bool,
    session_id: str,
    log_session_count: int,
    include_system_logs: bool,
    yes: bool,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Start-logging brain version", debug, output, test
        )

    if not managed_simulator and not session_id:
        raise_as_click_exception("\nFor an unmanaged simulator, session-id is requried")

    if not managed_simulator and include_system_logs:
        raise_as_click_exception(
            "\nIncluding system logs is currently only supported for managed simulators"
        )

    if not managed_simulator and all:
        raise_as_click_exception(
            "\nLogging all the simulators is currently only supported for managed simulators"
        )

    if all and log_session_count and log_session_count != 4:
        raise_as_click_exception(
            "\nYou can only set either --log-session-count or --all flag."
        )

    if not session_id:
        session_id = "0"

    if yes or not include_system_logs:
        is_confirmed = True
    else:
        is_confirmed = False

    if not is_confirmed and include_system_logs:
        click.echo(
            "Including system logs will cause some or all of your managed simulators to restart. Are you sure you want to start logging with system logs for brain {} version {} (y/n?).".format(
                name, version
            )
        )
        choice = input().lower()

        yes_set = {"yes", "y"}
        no_set = {"no", "n"}

        if choice in yes_set:
            is_confirmed = True
        elif choice in no_set:
            is_confirmed = False
        else:
            raise_as_click_exception("\nPlease respond with 'y' or 'n'")

    if is_confirmed:
        try:
            response = api(use_aad=True).start_logging(
                name,
                version=version,
                session_id=session_id,
                log_session_count=log_session_count,
                include_system_logs=include_system_logs,
                log_all_simulators=all,
                workspace=workspace_id,
                debug=debug,
            )

            status_message = "{} version {} logging started.".format(name, version)

            if output == "json":
                json_response = {
                    "status": response["status"],
                    "statusCode": response["statusCode"],
                    "statusMessage": status_message,
                }

                click.echo(dumps(json_response, indent=4))

            else:
                click.echo(status_message)

        except BrainServerError as e:
            if e.exception["statusCode"] == 404:
                raise_not_found_as_click_exception(
                    debug,
                    output,
                    "Start-logging brain version",
                    "Brain '{}' version".format(name),
                    "{}".format(version),
                    test,
                    e,
                )
            if "Current simulator count is 0" in e.exception["errorMessage"]:
                raise_as_click_exception(
                    "Cannot start logging when no simulators are connected. Connect unmanaged sims, or if you just started training, wait a few minutes and try again."
                )
            else:
                raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        except Exception as e:
            raise_client_side_click_exception(
                output, test, "{}: {}".format(type(e), e.args)
            )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command(
    "stop-logging",
    short_help="Stop logging for a simulator session.",
)
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version",
    type=int,
    help="Version to stop logging, defaults to latest.",
)
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--managed-simulator",
    "-m",
    type=str,
    default=False,
    is_flag=True,
    help="Please use this flag if this is for managed simulators.",
)
@click.option(
    "--session-id",
    "-d",
    help="Identifier for the simulator.",
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
def stop_logging(
    ctx: click.Context,
    name: str,
    version: int,
    workspace_id: str,
    managed_simulator: bool,
    session_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Stop-logging brain version", debug, output, test
        )

    if not managed_simulator and not session_id:
        raise_as_click_exception("\nFor an unmanaged simulator, session-id is requried")

    if not session_id:
        session_id = "0"

    try:
        response = api(use_aad=True).stop_logging(
            name,
            version=version,
            session_id=session_id,
            workspace=workspace_id,
            debug=debug,
        )

        status_message = "{} version {} logging stopped.".format(name, version)

        if output == "json":
            json_response = {
                "status": response["status"],
                "statusCode": response["statusCode"],
                "statusMessage": status_message,
            }

            click.echo(dumps(json_response, indent=4))

        else:
            click.echo(status_message)

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Start-logging brain version",
                "Brain '{}' version".format(name),
                "{}".format(version),
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("reset-training", short_help="Reset training for a brain version.")
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version", type=int, help="Version to reset training, defaults to latest."
)
@click.option(
    "--all", default=False, is_flag=True, help="Flag to reset all concepts and lessons."
)
@click.option(
    "--concept-name",
    "-c",
    help="Name of the concept to reset if you do not want to reset all concepts.",
)
@click.option(
    "--lesson-number",
    "-e",
    type=int,
    help="Lesson number to reset if you do not want to reset all lessons.",
)
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
def reset_training(
    ctx: click.Context,
    name: str,
    version: int,
    all: bool,
    concept_name: str,
    lesson_number: str,
    yes: bool,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    error_msg = ""
    required_options_provided = True

    if not name:
        required_options_provided = False
        error_msg += "\nName of the brain is required"

    if not all and not concept_name and not lesson_number:
        required_options_provided = False
        error_msg += (
            "\nEither specify the concept name and lesson number if you would like to reset a specific concept and lesson "
            "or the --all flag if you would like to reset all concepts and lessons"
        )

    if lesson_number and not concept_name:
        required_options_provided = False
        error_msg += "\nSpecify concept name to be used with the lesson number"

    if concept_name and not lesson_number:
        required_options_provided = False
        error_msg += "\nSpecify lesson number to be used with the concept name"

    if all and (concept_name or lesson_number):
        required_options_provided = False
        error_msg += (
            "\nSpecify the concept name and lesson number if you would like to reset a specific concept and lesson "
            "or the --all flag if you would like to reset all concepts and lessons, but not both"
        )

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    if not version:
        version = get_latest_brain_version(
            name, "Reset-training brain version", debug, output, test
        )

    is_reset = False

    if yes:
        is_reset = True

    if not yes:
        click.echo(
            "Are you sure you want to reset training for brain {} version {} (y/n?).".format(
                name, version
            )
        )
        choice = input().lower()

        yes_set = {"yes", "y"}
        no_set = {"no", "n"}

        if choice in yes_set:
            is_reset = True
        elif choice in no_set:
            is_reset = False
        else:
            raise_as_click_exception("\nPlease respond with 'y' or 'n'")

    if is_reset:
        try:
            response = api(use_aad=True).reset_training(
                name,
                version=version,
                all=all,
                concept_name=concept_name,
                lesson_number=lesson_number,
                workspace=workspace_id,
                debug=debug,
            )

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

        except BrainServerError as e:
            if e.exception["statusCode"] == 404:
                raise_not_found_as_click_exception(
                    debug,
                    output,
                    "Reset-training brain version",
                    "Brain '{}' version".format(name),
                    "{}".format(version),
                    test,
                    e,
                )
            else:
                raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        except Exception as e:
            raise_client_side_click_exception(
                output, test, "{}: {}".format(type(e), e.args)
            )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command(
    "start-assessing",
    deprecated=True,
    short_help="[DEPRECATED] Use 'bonsai brain version assessment start -h' to learn more about starting assessments",
)
def start_assessing():
    pass


@click.command(
    "stop-assessing",
    deprecated=True,
    short_help="[DEPRECATED] Use 'bonsai brain version assessment stop -h' to learn more about stopping assessments",
)
def stop_assessing():
    pass


@click.command(
    "diagnose",
    short_help="Checks the training health of a brain and its simulators. Requires access to additional Azure services and may prompt for credentials.",
    hidden=True,
)
@click.pass_context
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version", type=int, help="Version to check training health, defaults to latest."
)
@click.option(
    "--all", default=False, is_flag=True, help="Flag to reset all concepts and lessons."
)
@click.option("--concept-name", "-c", help="Concept to check.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--debug", default=False, is_flag=True, help="Verbose logging for request."
)
@click.option("--output", "-o", help="Set the output type, only 'zip' is supported.")
@click.option(
    "--test",
    default=False,
    is_flag=True,
    help="Enhanced response for testing.",
    hidden=True,
)
def diagnose_brain_version(
    ctx: click.Context,
    name: str,
    version: int,
    all: bool,
    concept_name: str,
    workspace_id: Optional[str],
    debug: bool,
    output: str,
    test: bool,
):

    # import the additional diaglets
    from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration
    from bonsai_cli.commands.diaglets.container_restarts import ContainerRestartsDiaglet
    from bonsai_cli.commands.diaglets.error_messages import ErrorsDiaglet
    from bonsai_cli.commands.diaglets.episode_logs_enabled import (
        EpisodeLogsEnabledDiaglet,
    )
    from bonsai_cli.commands.diaglets.iteration_halted import IterationHaltedDiaglet
    from bonsai_cli.commands.diaglets.last_n_records import LastNRecordsDiaglet
    from bonsai_cli.commands.diaglets.last_n_records import LastNRecordsDiaglet
    from bonsai_cli.commands.diaglets.sdk_version import SDKVersionDiaglet
    from bonsai_cli.commands.diaglets.sim_timeout import SimTimeoutDiaglet
    from bonsai_cli.commands.diaglets.sys_logs_enabled import SysLogsEnabledDiaglet

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the brain is required.")

    if not version:
        version = get_latest_brain_version(name, "diagnose brain", False, "", False)

    if not all and not concept_name:
        try:
            show_brain_version_response = api(use_aad=True).get_brain_version(
                name, version, workspace=workspace_id, debug=debug, output=output
            )

            if len(show_brain_version_response["concepts"]) > 0:
                concept_name = show_brain_version_response["concepts"][0]["name"]

            else:
                raise_as_click_exception(
                    "Concept name not provided and no concept name found in inkling"
                )

        except BrainServerError as e:
            if e.exception["statusCode"] == 404:
                raise_not_found_as_click_exception(
                    debug,
                    output,
                    "diagnose brain version",
                    "Brain '{}' version".format(name),
                    "{}".format(version),
                    test,
                    e,
                )
            else:
                raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        except Exception as e:
            raise_client_side_click_exception(
                output, test, "{}: {}".format(type(e), e.args)
            )

    if output and output != "zip":
        raise_as_click_exception("The output can only be 'zip'")

    bonsai_api = api(True)

    workspace = workspace_id if workspace_id else bonsai_api.workspace_id

    workspace_resources = bonsai_api.get_workspace_resources(workspace)

    diaglet_config = DiagletConfiguration()
    diaglet_config.brain_name = name
    diaglet_config.brain_version = version
    diaglet_config.concept_name = concept_name
    diaglet_config.is_test = test
    diaglet_config.unique_name = str(
        (datetime.now() - datetime(1, 1, 1)).total_seconds()
    ).replace(".", "")

    diaglet_config.workspace_id = workspace

    diaglet_config.subscription_id = workspace_resources["subscriptionId"]
    diaglet_config.managed_resource_group_name = workspace_resources[
        "serviceProvisionedResourceGroup"
    ]
    diaglet_config.log_analytics_workspace_id = workspace_resources[
        "logAnalyticsWorkspaceId"
    ]

    log_dir: str = ""

    # dont write files during the tests
    if not test:
        if not os.path.exists(diaglet_config.log_path):
            os.makedirs(diaglet_config.log_path)

        log_dir = os.path.join(diaglet_config.log_path, diaglet_config.unique_name)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    concepts: List[str] = []

    if not all:
        concepts.append(concept_name)
    else:
        try:
            # call the Bonsai API to get brain version details
            response: Any = api(use_aad=True).get_brain_version(
                name=diaglet_config.brain_name,
                version=diaglet_config.brain_version,
                workspace=diaglet_config.workspace_id,
            )

            for c in response["concepts"]:
                concepts.append(c["name"])

        except:
            raise_as_click_exception(
                f"Could not find details for {diaglet_config.workspace_id}/{diaglet_config.brain_name}/{diaglet_config.brain_version}"
            )

    print()
    print(
        f"Analyzing training diagnostics for brain {diaglet_config.brain_name}, version {diaglet_config.brain_version} ..."
    )

    for c in concepts:
        print()
        print(f"Diagnosing concept {c}:")
        print()

        diaglet_config.concept_name = c

        # the chain of diaglets to run. order is important because diaglets can stop processing the chain
        diaglet_chain = [
            ContainerRestartsDiaglet(diaglet_config),
            [
                SysLogsEnabledDiaglet(diaglet_config),
                SDKVersionDiaglet(diaglet_config),
                SimTimeoutDiaglet(diaglet_config),
                ErrorsDiaglet(diaglet_config),
            ],
            [
                EpisodeLogsEnabledDiaglet(diaglet_config),
                IterationHaltedDiaglet(diaglet_config),
            ],
        ]

        for diaglet in diaglet_chain:
            if isinstance(diaglet, Diaglet):
                break_chain = run_diaglet(diaglet)

                if break_chain:
                    print("Cannot continue diagnostics for this concept.\n")
                    break
            else:  # its a list
                for d in diaglet:
                    break_segment = run_diaglet(d)

                    if break_segment:
                        print(
                            "Cannot continue diagnostics in this segment for this concept.\n"
                        )
                        break

    if output == "zip":
        # also save the last N records in case the diaglets missed something
        last_n_records = LastNRecordsDiaglet(diaglet_config)
        last_n_records.diagnose()

        # zip up the files and delete the directory
        output_filename = os.path.join(
            diaglet_config.log_path, f"diagnostics_{diaglet_config.unique_name}"
        )

        shutil.make_archive(output_filename, "zip", log_dir)
        shutil.rmtree(log_dir)

        # notify the user where the files are
        print(f"All logs saved to {output_filename}.zip")

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


def run_diaglet(diaglet: Diaglet) -> bool:
    """
    runs the diaglet to get the output message and whether it should break the chain or segment it is in
    """
    diaglet.diagnose()

    print(f"{diaglet.friendly_name} -- {diaglet.message}\n")

    return diaglet.break_the_chain


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
version.add_command(start_logging)
version.add_command(stop_logging)
version.add_command(start_assessing)
version.add_command(stop_assessing)
version.add_command(start_logging)
version.add_command(stop_logging)
version.add_command(assessment)
version.add_command(diagnose_brain_version)
