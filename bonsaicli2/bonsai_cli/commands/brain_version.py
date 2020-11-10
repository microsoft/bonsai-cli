"""
This file contains the code for commands that target a bonsai brain version in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

import click
from json import dumps
from tabulate import tabulate

from bonsai_cli.api import BrainServerError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_not_found_as_click_exception,
    raise_client_side_click_exception,
)

from bonsai_cli.exceptions import AuthenticationError


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
            headers=["Version", "Training State", "Assessment State"],
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
        if not version:
            version = get_latest_brain_version(
                name, "Delete brain version", debug, output, test
            )

        try:
            response = api(use_aad=True).delete_brain_version(
                name, version=version, workspace=workspace_id, debug=debug
            )

            if response["statusCode"] == 204:
                raise_client_side_click_exception(
                    debug,
                    output,
                    test,
                    204,
                    "Brain '{}' version '{}' not found".format(name, version),
                    response,
                )

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

        if len(show_brain_version_response["concepts"]) > 0:
            concept_name = show_brain_version_response["concepts"][0]["name"]

        else:
            raise_as_click_exception(
                "Concept name not provided and no concept name found in inkling"
            )

    if instance_count and not simulator_package_name:
        raise_as_click_exception(
            "\nInstance count works only with a simulator package, please provide the name of the simulator package you would like to use"
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

    status_message = "{} version {} training stopped.".format(name, response["version"])

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
    "--session-id",
    "-d",
    help="Identifier for the simulator. This only applies to unmanaged simulators.",
)
@click.option(
    "--session-count",
    "-s",
    default=10,
    help="Number of simulators to enable logging for. This only applies to managed simulators. Default is 10.",
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
    session_id: str,
    session_count: int,
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

    if not session_id:
        session_id = "0"

    try:
        response = api(use_aad=True).start_logging(
            name,
            version=version,
            session_id=session_id,
            session_count=session_count,
            workspace=workspace_id,
            debug=debug,
        )

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
        if "reference" in e.exception["errorMessage"]:
            raise_as_click_exception(
                "\nThe simulator is not started yet, please try again later"
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

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

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command(
    "stop-logging",
    short_help="Stop logging for a simulator session.",
)
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version",
    type=int,
    help="[Required] Version to stop logging, defaults to latest.",
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

    is_delete = False

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
            is_delete = True
        elif choice in no_set:
            is_delete = False
        else:
            raise_as_click_exception("\nPlease respond with 'y' or 'n'")

    if is_delete:
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
@click.option(
    "--version", type=int, help="Version to start assessing, defaults to latest."
)
@click.option(
    "--simulator-package-name",
    help="Simulator package to use for assessing in the case of managed simulators.",
)
@click.option("--concept-name", "-c", help="Concept to assess.")
@click.option(
    "--instance-count",
    "-i",
    type=int,
    help="Number of instances to perform assessing with.",
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

    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the brain is required")

    if not version:
        version = get_latest_brain_version(
            name, "Start-assessing brain version", debug, output, test
        )

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
        if e.exception["statusCode"] == 404:
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
@click.option(
    "--version", type=int, help="Version to stop assessing, defaults to latest."
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
def stop_assessing(
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
            name, "Stop-assessing brain version", debug, output, test
        )

    try:
        response = api(use_aad=True).stop_assessment(
            name, version=version, workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
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


def get_latest_brain_version(
    name: str, operation: str, debug: bool, output: str, test: bool
):
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
