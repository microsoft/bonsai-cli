"""
This file contains the code for commands that target a bonsai simulator package in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

from typing import Any, Dict, List
import click
import os
import time

from json import dumps

from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_204_click_exception,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_client_side_click_exception,
    raise_not_found_as_click_exception,
)

from .simulator_package_container import container
from .simulator_package_modelfile import modelfile


@click.group()
def package():
    """Simulator package operations."""
    pass


"""
This model file upload command is just for internal usage and hence hidden flag is set to true
"""


@click.command(
    "upload",
    short_help="Upload Simulator Package Model file providing the complete file path",
    hidden=True,
)
@click.option(
    "--modelfilepath", "-m", help="[Required] Model File Path on local system."
)
@click.option(
    "--debug", default=False, is_flag=True, help="Verbose logging for request."
)
@click.option("--output", "-o", help="Set output, only json supported.")
@click.pass_context
def upload_model_file(
    ctx: click.Context, modelfilepath: str, debug: bool, output: bool
):

    version_checker = get_version_checker(ctx, interactive=not output)

    try:
        tic = time.perf_counter()
        response = api(use_aad=True).upload_model_file(modelfilepath, debug=debug)
        toc = time.perf_counter()
        size = os.path.getsize(modelfilepath)
        print(
            "*******************************************************************************************************"
        )
        print(
            f"uploaded {modelfilepath} of size:{size*0.000001} MB in {toc - tic:0.4f} seconds."
        )
        print(
            "*******************************************************************************************************"
        )
    except AuthenticationError as e:
        raise_as_click_exception(e)

    status_message = "Uploaded model file {} successfully.".format(
        response["uploadedFileName"]
    )

    if output == "json":
        json_response = {
            "uploadedFileName": response["uploadedFileName"],
            "uploadedFileStoragePath": response["modelFileStoragePath"],
            "createdTimeStamp": response["createdTimeStamp"],
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": status_message,
        }
        click.echo(dumps(json_response, indent=4))

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about a simulator package.")
@click.option(
    "--name",
    "-n",
    help="[Required] The name of the simulator package to show.",
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
def show_simulator_package(
    ctx: click.Context,
    name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("\nName of the simulator package is required")

    try:
        response = api(use_aad=True).get_sim_package(
            name, workspace=workspace_id, debug=debug, output=output
        )

        if output == "json":
            json_response = {
                "status": response["status"],
                "statusCode": response["statusCode"],
                "statusMessage": {
                    "name": response["name"],
                    "status": response["operationStatus"],
                    "acrUri": response["imagePath"],
                    "cores": response["coresPerInstance"],
                    "memory": response["memInGbPerInstance"],
                    "instanceCount": response["startInstanceCount"],
                },
            }

            click.echo(dumps(json_response, indent=4))

        else:
            click.echo("Name: {}".format(response["name"]))
            click.echo("Status: {}".format(response["operationStatus"]))
            click.echo("ACR Uri: {}".format(response["imagePath"]))
            click.echo("Cores (in vCPU): {}".format(response["coresPerInstance"]))
            click.echo("Memory (in GB): {}".format(response["memInGbPerInstance"]))
            click.echo("Instance Count: {}".format(response["startInstanceCount"]))

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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("update", short_help="Update information about a simulator package.")
@click.option("--name", "-n", help="[Required] Name of the simulator package.")
@click.option(
    "--instance-count",
    "-i",
    type=int,
    help="Number of instances to perform training with the simulator package.",
)
@click.option(
    "--cores-per-instance",
    "-r",
    type=float,
    help="Number of cores that should be allocated for each simulator instance.",
)
@click.option(
    "--memory-in-gb-per-instance",
    "-m",
    type=float,
    help="Memory in GB that should be allocated for each simulator instance.",
)
@click.option("--display-name", help="Display name of the simulator package.")
@click.option("--description", help="Description for the simulator package.")
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
    version_checker = get_version_checker(ctx, interactive=not output)

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

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("list", short_help="Lists simulator packages owned by current user.")
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
def list_simulator_package(
    ctx: click.Context, workspace_id: str, debug: bool, output: str, test: bool
):
    version_checker = get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_sim_package(
            workspace=workspace_id, debug=debug
        )

        if len(response["value"]) == 0:
            click.echo("No simulator packages exist for the current user")
            ctx.exit()

        if output == "json":
            dict_rows: List[Dict[str, Any]] = []
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

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

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
def remove_simulator_package(
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
        raise_as_click_exception("\nName of the simulator package is required")

    is_delete = False

    if yes:
        is_delete = True

    if not yes:
        click.echo(
            "Are you sure you want to remove simulator package {} (y/n?).".format(name)
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

            if response["statusCode"] == 204:
                raise_204_click_exception(
                    debug,
                    output,
                    test,
                    204,
                    "Simulator package '{}' not found".format(name),
                    response,
                )

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

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


package.add_command(upload_model_file)
package.add_command(show_simulator_package)
package.add_command(update_simulator_package)
package.add_command(list_simulator_package)
package.add_command(remove_simulator_package)
package.add_command(container)
package.add_command(modelfile)
