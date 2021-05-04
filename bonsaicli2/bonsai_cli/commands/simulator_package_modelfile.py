"""
This file contains the code for commands that target a bonsai model file simulator package in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2021, Microsoft Corp."

from typing import Any, Dict, List
import click
import os
import time

from json import dumps
from tabulate import tabulate

from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_client_side_click_exception,
    raise_unique_constraint_violation_as_click_exception,
)


@click.group()
def modelfile():
    """Model file simulator package operations."""
    pass


@click.command("create", short_help="Create a modelfile simulator package.")
@click.option(
    "--name", "-n", help="[Required] Name of the modelfile simulator package."
)
@click.option(
    "--file",
    "-f",
    help="[Required] Path to zip file of the simulation model to upload as a modelfile simulator package.",
)
@click.option(
    "--base-image",
    help="[Required] The simulator base_image you would like to use. Run 'bonsai simulator package modelfile list-base-image' to get the list of accepted simulator base_images.",
)
@click.option(
    "--instance-count",
    "-i",
    type=int,
    help="Number of instances to start and perform training with the modelfile simulator package.",
)
@click.option(
    "--min-instance-count",
    type=int,
    help="Minimum Number of instances to perform training with the modelfile simulator package.",
)
@click.option(
    "--max-instance-count",
    type=int,
    help="Maximum Number of instances to perform training with the modelfile simulator package.",
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
@click.option(
    "--auto-scale",
    type=bool,
    help="Flag to indicate scale up or scale down simulators. By default, it is set to true",
    default=True,
)
@click.option("--display-name", help="Display name of the modelfile simulator package.")
@click.option("--description", help="Description for the modelfile simulator package.")
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
def create_modelfile_simulator_package(
    ctx: click.Context,
    name: str,
    file: str,
    base_image: str,
    instance_count: int,
    min_instance_count: int,
    max_instance_count: int,
    cores_per_instance: float,
    memory_in_gb_per_instance: float,
    auto_scale: bool,
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
        error_msg += "\nName of the modelfile simulator package is required"

    if not file:
        required_options_provided = False
        error_msg += "\nPath to zip file of the simulation model to upload as a modelfile simulator package is required"

    if not base_image:
        required_options_provided = False
        error_msg += "\nBase image details are required"

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    try:
        get_sim_base_image_response = api(use_aad=True).get_sim_base_image(
            base_image, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_as_click_exception(
                "Base image {} is invalid, run 'bonsai simulator package modelfile list-base-image' to get the list of accepted simulator base_images.".format(
                    base_image
                )
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    if not instance_count:
        instance_count = get_sim_base_image_response["startInstanceCount"]

    if not min_instance_count:
        min_instance_count = get_sim_base_image_response["minInstanceCount"]

    if not max_instance_count:
        max_instance_count = get_sim_base_image_response["maxInstanceCount"]

    if not cores_per_instance:
        cores_per_instance = get_sim_base_image_response["coresPerInstanceRecommended"]

    if not memory_in_gb_per_instance:
        memory_in_gb_per_instance = get_sim_base_image_response[
            "memInGBPerInstanceRecommended"
        ]

    try:
        tic = time.perf_counter()

        upload_model_file_response = api(use_aad=True).upload_model_file(
            file, debug=debug
        )

        toc = time.perf_counter()
        size = os.path.getsize(file)
        print(
            "*******************************************************************************************************"
        )
        print(
            f"uploaded {file} of size:{size * 0.000001} MB in {toc - tic:0.4f} seconds."
        )
        print(
            "*******************************************************************************************************"
        )

    except BrainServerError as e:
        raise_as_click_exception(e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    try:
        sim_package_response = api(use_aad=True).create_sim_package(
            name=name,
            model_file_path=upload_model_file_response["modelFileStoragePath"],
            model_base_image_name=base_image,
            start_instance_count=instance_count,
            min_instance_count=min_instance_count,
            max_instance_count=max_instance_count,
            cores_per_instance=cores_per_instance,
            memory_in_gb_per_instance=memory_in_gb_per_instance,
            auto_scale=auto_scale,
            # set auto terminate to true by default
            auto_terminate=True,
            display_name=display_name,
            description=description,
            os_type="linux",
            package_type="modelfile",
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

        status_message = "Created new modelfile simulator package {}. Run 'bonsai simulator package show -n {}' to get the status of the simulator package.".format(
            sim_package_response["name"], sim_package_response["name"]
        )

        if output == "json":
            json_response = {
                "status": sim_package_response["status"],
                "statusCode": sim_package_response["statusCode"],
                "statusMessage": status_message,
            }

            click.echo(dumps(json_response, indent=4))

        else:
            click.echo(status_message)

    except BrainServerError as e:
        if "Unique index constraint violation" in str(e):
            raise_unique_constraint_violation_as_click_exception(
                debug, output, "Modelfile simulator package", name, test, e
            )
        else:
            raise_as_click_exception(e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command(
    "list-base-image", short_help="List base images for modelfile simulator packages."
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
def list_base_image_modelfile_simulator_package(
    ctx: click.Context,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_sim_base_images(
            workspace=workspace_id, debug=debug, output=output
        )

        rows: List[Any] = []
        dict_rows: List[Dict[str, Any]] = []
        for item in response["value"]:
            try:
                base_image = item["imageIdentifier"]
                cores_per_instance = item["coresPerInstanceRecommended"]
                memory_in_gb_per_instance = item["memInGBPerInstanceRecommended"]
                start_instance_count = item["startInstanceCount"]
                min_instance_count = item["minInstanceCount"]
                max_instance_count = item["maxInstanceCount"]
                rows.append(
                    [
                        base_image,
                        cores_per_instance,
                        memory_in_gb_per_instance,
                        start_instance_count,
                        min_instance_count,
                        max_instance_count,
                    ]
                )
                dict_rows.append(
                    {
                        "baseImage": base_image,
                        "defaultCoresPerInstance": cores_per_instance,
                        "defaultMemoryInGBPerInstance": memory_in_gb_per_instance,
                        "defaultStartInstanceCount": start_instance_count,
                        "defaultMinInstanceCount": min_instance_count,
                        "defaultMaxInstanceCount": max_instance_count,
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
                headers=[
                    "Base Image",
                    "Default Cores Per Instance",
                    "Default Memory in GB Per Instance",
                    "Default Start Instance Count",
                    "Default Min Instance Count",
                    "Default Max Instance Count",
                ],
                tablefmt="orgtbl",
            )
            click.echo(table)

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    except Exception as e:
        raise_client_side_click_exception(
            output, test, "{}: {}".format(type(e), e.args)
        )

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


modelfile.add_command(create_modelfile_simulator_package)
modelfile.add_command(list_base_image_modelfile_simulator_package)
