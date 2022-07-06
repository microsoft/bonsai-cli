"""
This file contains the code for commands that target a deploying a webapp for a bonsai exported brain in version 2 of the bonsai command line.
"""
__author__ = "David Coe"
__copyright__ = "Copyright 2022, Microsoft Corp."

from typing import Any, Dict, Iterable
import click
import re
from json import dumps

from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_unique_constraint_violation_as_click_exception,
    raise_not_found_as_click_exception,
)


@click.group()
def webapp():
    """Exportedbrain deploy webapp operations"""
    pass


@click.command(
    "create", short_help="Create a web app cloud deployment for an exported brain."
)
@click.pass_context
@click.option("--name", "-n", help="[Required] Name of the web app to be created.")
@click.option(
    "--exported-brain-name", help="[Required] Name of the exported brain to deploy."
)
@click.option("--display-name", help="Display name of the cloud deployment.")
@click.option("--description", help="Description for the cloud deployment.")
@click.option(
    "--location",
    help="The Azure region to deploy the web app (must be the same region if re-using an existing App Service Plan).",
)
@click.option(
    "--app-service-plan-name",
    help="Existing or new name of the App Service Plan (in the Bonsai-managed resource group).",
)
@click.option(
    "--azure-ad-app-id",
    help="The Azure AD application ID to use to secure your web app deployment.",
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
def create_webapp(
    ctx: click.Context,
    name: str,
    exported_brain_name: str,
    display_name: str,
    description: str,
    location: str,
    app_service_plan_name: str,
    azure_ad_app_id: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception(
            "Name of the web app deployment is required. Only alphanumerics or hyphens are allowed."
        )

    #
    # the name must conform to the Microsoft.Web/sites naming convention outlined at https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules#microsoftweb
    #
    regex = re.compile(r"^[a-zA-Z0-9\-]*$")

    if (
        regex.fullmatch(name) is None
        or len(name) < 2
        or len(name) > 60
        or name[1:] == "-"
        or name[:1] == "-"
    ):
        raise_as_click_exception(
            "A deployment name must be 2-60 characters containing alphanumeric characters and an optional dash '-' character. The name may not start or end with a dash."
        )

    if not exported_brain_name:
        raise_as_click_exception("Name of the exported brain is required")

    #
    # ensure the user isnt passing their full acr path as the exported brain name
    #
    if ".azurecr.io" in exported_brain_name.lower():
        raise_as_click_exception(
            "Please use the name of the exported brain, not the full container path."
        )

    #
    # check if the exported brain specified exists
    #
    try:
        response = api(use_aad=True).get_exported_brain(
            name=exported_brain_name,
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "webapp create",
                "Exported brain",
                exported_brain_name,
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    try:
        response = api(use_aad=True).create_webapp_deployment(
            name=name,
            exported_brain_name=exported_brain_name,
            display_name=display_name,
            description=description,
            app_service_plan_name=app_service_plan_name,
            azure_ad_app_id=azure_ad_app_id,
            location=location,
            workspace=workspace_id,
            debug=debug,
        )
    except BrainServerError as e:
        if "Unique index constraint violation" in str(e):
            raise_unique_constraint_violation_as_click_exception(
                debug, output, "Cloud deployment", name, test, e
            )
        else:
            raise_as_click_exception(e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    secured = False

    if response["azureAdApplicationId"] != "":
        secured = True

    if output == "json":
        json_response = {
            "name": response["name"],
            "displayName": response["displayName"],
            "resourceGroupName": response["resourceGroupName"],
            "appServicePlanName": response["appServicePlanName"],
            "hostName": response["hostName"],
            "deploymentStatus": response["deploymentStatus"],
            "securedOnCreate": secured,
            "statusCode": response["statusCode"],
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo("Name: {}".format(response["name"]))
        click.echo("Display Name: {}".format(response["displayName"]))
        click.echo("Resource group: {}".format(response["resourceGroupName"]))
        click.echo("App Service Plan: {}".format(response["appServicePlanName"]))
        click.echo("Secured During Create: {}".format(secured))
        click.echo("HostName: {}".format(response["hostName"]))
        click.echo("Deployment Status: {}".format(response["deploymentStatus"]))

        if response["deploymentStatus"] == "Completed":
            click.echo()
            click.echo(
                "Open your browser to https://{}/swagger.html to review documentation for calling your newly deployed brain.".format(
                    response["hostName"]
                )
            )

        click.echo()

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("list", short_help="Lists web app deployments.")
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
def list_webapp(
    ctx: click.Context, workspace_id: str, debug: bool, output: str, test: bool
):
    version_checker = get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_webapp_deployments(
            workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if len(response["value"]) == 0:
        click.echo("No cloud deployments exist for the current user")
        ctx.exit()

    if output == "json":

        result: Dict[str, Any] = {}

        json_responses: Iterable[Dict[str, Any]] = []

        for cd in response["value"]:
            json_response = {"name": cd["name"]}
            json_responses.append(json_response)

        result["value"] = json_responses
        result["statusCode"] = response["statusCode"]

        if test:
            result["elapsed"] = str(response["elapsed"])
            result["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(result, indent=4))

    else:
        for clouddeployment in response["value"]:
            click.echo(clouddeployment["name"])

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about a web app deployment.")
@click.option("--name", "-n", help="[Required] Name of the web app deployment.")
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
def show_webapp(
    ctx: click.Context,
    name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the cloud deployment is required")

    try:
        response = api(use_aad=True).get_webapp_deployment(
            name, workspace=workspace_id, debug=debug
        )

    except BrainServerError as e:
        if "not found" in str(e):
            raise_not_found_as_click_exception(
                debug, output, "show", "cloud deployment", name, test, e
            )

        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    secured = False

    if response["azureAdApplicationId"] != "":
        secured = True

    if output == "json":
        json_response = {
            "name": response["name"],
            "displayName": response["displayName"],
            "resourceGroupName": response["resourceGroupName"],
            "appServicePlanName": response["appServicePlanName"],
            "hostName": response["hostName"],
            "deploymentStatus": response["deploymentStatus"],
            "securedOnCreate": secured,
            "statusCode": response["statusCode"],
        }

        if test:
            json_response["elapsed"] = str(response["elapsed"])
            json_response["timeTaken"] = str(response["timeTaken"])

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo("Name: {}".format(response["name"]))
        click.echo("Display Name: {}".format(response["displayName"]))
        click.echo("Resource group: {}".format(response["resourceGroupName"]))
        click.echo("App Service Plan: {}".format(response["appServicePlanName"]))
        click.echo("Secured During Create: {}".format(secured))
        click.echo("HostName: {}".format(response["hostName"]))
        click.echo("Deployment Status: {}".format(response["deploymentStatus"]))

        if response["deploymentStatus"] == "Completed":
            click.echo()
            click.echo(
                "Open your browser to https://{}/swagger.html to review documentation for calling your deployed brain.".format(
                    response["hostName"]
                )
            )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("delete", short_help="Delete a web app deployment.")
@click.option("--name", "-n", help="[Required] Name of the web app deployment.")
@click.option(
    "--include-azure-resources",
    default=True,
    help="Delete the Azure resources created by web app deployment. True by default.",
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
def delete_webapp(
    ctx: click.Context,
    name: str,
    include_azure_resources: bool,
    yes: bool,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the cloud deployment is required")

    is_delete = False

    if yes:
        is_delete = True

    if not yes:
        click.echo(
            "Are you sure you want to delete web app deployment {} (y/n?).".format(name)
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
            response = api(use_aad=True).delete_webapp_deployment(
                name,
                includeAzureResources=include_azure_resources,
                workspace=workspace_id,
                debug=debug,
                output=output,
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


webapp.add_command(create_webapp)
webapp.add_command(show_webapp)
webapp.add_command(list_webapp)
webapp.add_command(delete_webapp)
