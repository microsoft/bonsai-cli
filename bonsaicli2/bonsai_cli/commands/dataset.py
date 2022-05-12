"""
This file contains the code for commands that target a bonsai dataset in version 2 of the bonsai command line.
"""
__author__ = "Mayank Gupta"
__copyright__ = "Copyright 2020, Microsoft Corp."

from typing import Any, Dict, List
import click
from json import dumps

from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_not_found_as_click_exception,
    raise_client_side_click_exception,
    raise_204_click_exception,
)

from .dataset_aml import aml


@click.group(hidden=True)
def dataset():
    """dataset operations."""
    pass


@click.command("list", short_help="Lists datasets owned by current user.")
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
def list_dataset(
    ctx: click.Context, workspace_id: str, debug: bool, output: str, test: bool
):
    version_checker = get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_dataset(
            workspace=workspace_id, debug=debug, output=output
        )

        if len(response["value"]) == 0:
            click.echo("No datasets exist for the current user")
            ctx.exit()

        if output == "json":
            dict_rows: List[Dict[str, Any]] = []
            for dataset in response["value"]:
                dict_rows.append(dataset["name"])

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
            for dataset in response["value"]:
                click.echo(dataset["name"])

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    except Exception as e:
        if e.args[0] != 0:
            raise_client_side_click_exception(
                output, test, "{}: {}".format(type(e), e.args)
            )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about a dataset.")
@click.option("--name", "-n", help="[Required] Name of the dataset.")
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
def show_dataset(
    ctx: click.Context,
    name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the dataset is required")

    try:
        response = api(use_aad=True).get_dataset(
            name,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

        if output == "json":
            json_response = {
                "name": response["name"],
                "displayName": response["displayName"],
                "description": response["description"],
                "dataSourceType": response["dataSourceType"],
                "dataStoreType": response["dataStoreType"],
                "connectionString": response["connectionString"],
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
            click.echo("DataSourceType: {}".format(response.get("dataSourceType", "")))
            click.echo("DataStoreType: {}".format(response["dataStoreType"]))
            click.echo("ConnectionString: {}".format(response["connectionString"]))

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug, output, "Show dataset", "dataset", name, test, e
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


@click.command("delete", short_help="Delete a dataset.")
@click.option("--name", "-n", help="[Required] Name of the dataset.")
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
def delete_dataset(
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
        raise_as_click_exception("Name of the dataset is required")

    is_delete = False

    if yes:
        is_delete = True

    if not yes:
        click.echo("Are you sure you want to delete dataset {} (y/n?).".format(name))
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
            response = api(use_aad=True).delete_dataset(
                name,
                workspace=workspace_id,
                debug=debug,
                output=output,
            )

            if response["statusCode"] == 204:
                raise_204_click_exception(
                    debug,
                    output,
                    test,
                    204,
                    "dataset '{}' not found".format(name),
                    response,
                )

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

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


dataset.add_command(aml)
dataset.add_command(show_dataset)
dataset.add_command(list_dataset)
dataset.add_command(delete_dataset)
