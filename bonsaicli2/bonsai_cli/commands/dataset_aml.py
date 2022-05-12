"""
This file contains the code for commands that target a bonsai dataset in version 2 of the bonsai command line.
"""
__author__ = "Mayank Gupta"
__copyright__ = "Copyright 2020, Microsoft Corp."

import click
from json import dumps

from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_unique_constraint_violation_as_click_exception,
    raise_client_side_click_exception,
)


@click.group()
def aml():
    """azure machine learning dataset operations."""
    pass


@click.command("create", short_help="Create an Azure Machine Learning dataset.")
@click.pass_context
@click.option("--name", "-n", help="[Required] Name of the dataset.")
@click.option("--display-name", help="Display name of the dataset.")
@click.option("--description", help="Description for the dataset.")
@click.option("--subscription_id", help="Azure subscription Id")
@click.option("--resource_group", help="azure resource group")
@click.option("--aml_workspace", help="AML workspace name")
@click.option("--aml_dataset_name", help="AML dataset name")
@click.option("--aml_datastore_name", help="AML datastore name")
@click.option("--aml_version", help="AML data version")
@click.option(
    "--data_source_type",
    help="Source of the data",
    type=click.Choice(["User", "DeployedBrain"]),
    default="User",
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
def create_aml_dataset(
    ctx: click.Context,
    name: str,
    display_name: str,
    description: str,
    workspace_id: str,
    subscription_id: str,
    resource_group: str,
    data_source_type: str,
    aml_workspace: str,
    aml_dataset_name: str,
    aml_datastore_name: str,
    aml_version: int,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the dataset is required")

    if not subscription_id:
        raise_as_click_exception("subscription_id is required")

    if not resource_group:
        raise_as_click_exception("resource_group is required")

    if not aml_workspace:
        raise_as_click_exception("aml_workspace is required")

    if not aml_dataset_name:
        raise_as_click_exception("aml_dataset_name is required")

    if not aml_datastore_name:
        raise_as_click_exception("aml_datastore_name is required")

    if not aml_version:
        raise_as_click_exception("aml_version is required")

    try:
        response = api(use_aad=True).create_aml_dataset(
            name=name,
            subscription_id=subscription_id,
            resource_group=resource_group,
            display_name=display_name,
            description=description,
            workspace=workspace_id,
            data_source_type=data_source_type,
            data_store_type="Aml",
            aml_workspace=aml_workspace,
            aml_dataset_name=aml_dataset_name,
            aml_datastore_name=aml_datastore_name,
            aml_version=aml_version,
            debug=debug,
            output=output,
        )

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

    except BrainServerError as e:
        if "Unique index constraint violation" in str(e):
            raise_unique_constraint_violation_as_click_exception(
                debug, output, "Brain", name, test, e
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


aml.add_command(create_aml_dataset)
