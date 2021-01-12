"""
This file contains the code for commands that target a bonsai imported model in version 2 of the bonsai command line.
"""
__author__ = "Anil Puvvadi"
__copyright__ = "Copyright 2020, Microsoft Corp."

import click
import os
import time

from json import dumps

from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_unique_constraint_violation_as_click_exception,
    raise_not_found_as_click_exception,
    raise_client_side_click_exception,
)


@click.group(hidden=True)
def importedmodel():
    """Imported model operations."""
    pass


@click.command("create", short_help="Create a imported model.")
@click.option("--name", "-n", help="[Required] Name of the imported model.")
@click.option("--modelfilepath", "-m", help="[Required] ModelFilePath on local system.")
@click.option("--display-name", "-dn", help="Display name of the imported model.")
@click.option("--description", "-des", help="Description for the imported model.")
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
def create_importedmodel(
    ctx: click.Context,
    name: str,
    modelfilepath: str,
    display_name: str,
    description: str,
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
        error_msg += "\nImported model name is required"

    if not modelfilepath:
        required_options_provided = False
        error_msg += "\nModelfilepath is required"

    if not display_name:
        required_options_provided = False
        error_msg += "\nDisplayName for the imported model is required"

    if not description:
        required_options_provided = False
        error_msg += "\nDescription for the imported model is required"

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    try:
        tic = time.perf_counter()
        response = api(use_aad=True).upload_importedmodel(
            name, modelfilepath, debug=debug
        )
        toc = time.perf_counter()
        size = os.path.getsize(modelfilepath)

        print(
            f"step 1: Uploading {modelfilepath} of size:{size*0.000001} MB is successful in {toc - tic:0.4f} seconds."
        )

        print("step 2: Finalizing the upload..This may take a while. Please wait...")

        response = api(use_aad=True).create_importedmodel(
            name=name,
            uploaded_file_path=response["modelFileStoragePath"],
            display_name=display_name,
            description=description,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

        while response["operationStatus"] not in ["Succeeded", "Failed"]:
            print(
                "step 2: Finalizing the upload. The current status is "
                + response["operationStatus"]
                + ". Please wait..."
            )
            response = api(use_aad=True).get_importedmodel(
                name=name, workspace=workspace_id
            )
            time.sleep(10)

        if response["operationStatus"] == "Succeeded":
            statusMessage = "Created new imported model {} successfully.".format(
                response["name"]
            )

        elif response["operationStatus"] == "Failed":
            statusMessage = "Failed to create new imported model {}. Please contact Bonsai Service Team.".format(
                response["name"]
            )
        else:
            statusMessage = "Status unknown for imported model {} upload .Please contact Bonsai Service Team.".format(
                response["name"]
            )

        if output == "json":
            json_response = {
                "status": response["operationStatus"],
                "statusCode": response["statusCode"],
                "statusMessage": statusMessage,
            }
            click.echo(dumps(json_response, indent=4))
        else:
            click.echo(statusMessage)

    except BrainServerError as e:
        if "Unique index constraint violation" in str(e):
            raise_unique_constraint_violation_as_click_exception(
                debug, output, "Imported model", name, test, e
            )
        else:
            raise_as_click_exception(e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about imported model.")
@click.option(
    "--name",
    "-n",
    help="[Required] The name of the imported model to show.",
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
def show_importedmodel(
    ctx: click.Context,
    name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the imported model is required")

    try:
        response = api(use_aad=True).get_importedmodel(
            name, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Show imported model",
                "Imported model",
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
            "status": response["operationStatus"],
            "statusCode": response["statusCode"],
            "statusMessage": {
                "id": response["id"],
                "name": response["name"],
                "displayName": response["displayName"],
                "description": response["description"],
                "importedModelType": response["importedModelType"],
                "createdTimeStamp": response["createdTimeStamp"],
                "modifedTimeStamp": response["modifedTimeStamp"],
            },
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo("Id: {}".format(response["id"]))
        click.echo("Name: {}".format(response["name"]))
        click.echo("DISPLAY NAME: {}".format(response["displayName"]))
        click.echo("DESCRIPTION: {}".format(response["description"]))
        click.echo("IMPORTED MODEL TYPE: {}".format(response["importedModelType"]))
        click.echo("CREATED TIMESTAMP: {}".format(response["createdTimeStamp"]))
        click.echo("MODIFIED TIMESTAMP: {}".format(response["modifedTimeStamp"]))

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("update", short_help="Update information about a imported model")
@click.option("--name", "-n", help="[Required] Name of the imported model.")
@click.option("--display-name", "-dn", help="Display name of the imported model.")
@click.option("--description", "-des", help="Description for the imported model.")
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
def update_importedmodel(
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
        raise_as_click_exception("\nName of the imported model is required")

    if not (display_name or description):
        raise_as_click_exception(
            "\nDisplay Name or description for the imported model must be updated."
        )

    try:
        response = api(use_aad=True).update_importedmodel(
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
                debug,
                output,
                "Update imported model",
                "ImportedModel",
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
            "status": response["operationStatus"],
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


@click.command("list", short_help="Lists imported model owned by current user.")
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
def list_importedmodel(
    ctx: click.Context, workspace_id: str, debug: bool, output: str, test: bool
):
    version_checker = get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_importedmodels(
            workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if len(response["value"]) == 0:
        click.echo("No imported models exist for the current user")
        ctx.exit()

    if output == "json":
        dict_rows = []
        for imported_model in response["value"]:
            dict_rows.append(imported_model["name"])

        json_response = {
            "value": dict_rows,
            "status": response["operationStatus"],
            "statusCode": response["statusCode"],
            "statusMessage": "",
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        for imported_model in response["value"]:
            click.echo(imported_model["name"])

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("delete", short_help="Delete a imported model.")
@click.option(
    "--name",
    "-n",
    help="[Required] The name of the imported model to delete.",
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
def delete_importedmodel(
    ctx: click.Context,
    name: str,
    yes: bool,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=True)

    if not name:
        raise_as_click_exception("\nName of the imported model is required")

    is_delete = False

    if yes:
        is_delete = True

    if not yes:
        click.echo(
            "Are you sure you want to delete IMPORTED model {} (y/n?).".format(name)
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
            response = api(use_aad=True).delete_importedmodel(
                name, workspace=workspace_id, debug=debug
            )

            if response["statusCode"] == 204:
                raise_client_side_click_exception(
                    debug,
                    output,
                    test,
                    204,
                    "Imported model '{}' not found".format(name),
                    response,
                )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        status_message = "{} deleted.".format(name)

        if output == "json":
            json_response = {
                "status": response["operationStatus"],
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


importedmodel.add_command(create_importedmodel)
importedmodel.add_command(show_importedmodel)
importedmodel.add_command(update_importedmodel)
importedmodel.add_command(list_importedmodel)
importedmodel.add_command(delete_importedmodel)
