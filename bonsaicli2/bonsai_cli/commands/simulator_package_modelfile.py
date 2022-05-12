"""
This file contains the code for commands that target a bonsai model file simulator package in version 2 of the bonsai command line.
"""
__author__ = "Anil Puvvadi, Karthik Sankara Subramanian"
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
    "--os-type",
    "-p",
    help="[Required] OS type for the model file simulator package. Windows or Linux.",
    type=click.Choice(["Windows", "Linux"], case_sensitive=False),
)
@click.option(
    "--max-instance-count",
    type=int,
    help="Maximum Number of instances to perform training with the modelfile simulator package.",
)
@click.option(
    "--spot-percent",
    type=click.IntRange(0, 90),
    default=0,
    help="Percentage of maximum instance count of managed simulators that will use spot pricing. Note that the maximum allowed spot percent is 90%",
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
@click.option("--display-name", help="Display name of the modelfile simulator package.")
@click.option("--description", help="Description for the modelfile simulator package.")
@click.option(
    "--workspace-id",
    "-w",
    help="Please provide the workspace id if you would like to override the default target workspace. If your current Azure Active Directory login does not have access to this workspace, you will need to configure the workspace using bonsai configure.",
)
@click.option(
    "--compute-type",
    default="AzureContainerInstance",
    help="(experimental) select the simulator compute infrastructure. choose from [AzureContainerInstance (default) | AzureKubernetesService]",
    hidden=True,
)
@click.option(
    "--managed-app-resourcegroup-name",
    help="ManagedApp ResourceGroupName under which managed app is currently running for the offer chosen.",
    hidden=True,
)
@click.option(
    "--managed-app-name",
    help="ManagedApp Name currently running under customer subscription for the offer chosen.",
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
def create_modelfile_simulator_package(
    ctx: click.Context,
    name: str,
    file: str,
    base_image: str,
    max_instance_count: int,
    spot_percent: int,
    cores_per_instance: float,
    memory_in_gb_per_instance: float,
    display_name: str,
    description: str,
    workspace_id: str,
    compute_type: str,
    managed_app_resourcegroup_name: str,
    managed_app_name: str,
    os_type: str,
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

    if not os_type:
        required_options_provided = False
        error_msg += "\nOS Type is required"

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

    if not max_instance_count:
        max_instance_count = get_sim_base_image_response["maxInstanceCount"]

    if not cores_per_instance:
        cores_per_instance = get_sim_base_image_response["coresPerInstanceRecommended"]

    if not memory_in_gb_per_instance:
        memory_in_gb_per_instance = get_sim_base_image_response[
            "memInGBPerInstanceRecommended"
        ]

    publisher_id = ""
    offer_id = ""
    plan_id = ""
    meter_id = ""
    part_number = ""

    if "publisherId" in get_sim_base_image_response:
        publisher_id = get_sim_base_image_response["publisherId"]
    if "offerId" in get_sim_base_image_response:
        offer_id = get_sim_base_image_response["offerId"]
    if "planId" in get_sim_base_image_response:
        plan_id = get_sim_base_image_response["planId"]
    if "meterId" in get_sim_base_image_response:
        meter_id = get_sim_base_image_response["meterId"]
    if "partNumber" in get_sim_base_image_response:
        part_number = get_sim_base_image_response["partNumber"]

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
            max_instance_count=max_instance_count,
            spot_percent=spot_percent,
            cores_per_instance=cores_per_instance,
            memory_in_gb_per_instance=memory_in_gb_per_instance,
            display_name=display_name,
            description=description,
            os_type=os_type,
            package_type="modelfile",
            workspace=workspace_id,
            compute_type=compute_type,
            publisher_id=publisher_id,
            offer_id=offer_id,
            plan_id=plan_id,
            meter_id=meter_id,
            part_number=part_number,
            managed_app_resourcegroup_name=managed_app_resourcegroup_name,
            managed_app_name=managed_app_name,
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
            raise_brain_server_error_as_click_exception(debug, output, test, e)

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
                os_type = "NA"
                publisher_id = "NA"
                offer_id = "NA"
                plan_id = "NA"
                meter_id = "NA"
                part_number = "NA"

                base_image = item["imageIdentifier"]
                cores_per_instance = item["coresPerInstanceRecommended"]
                memory_in_gb_per_instance = item["memInGBPerInstanceRecommended"]
                start_instance_count = item["startInstanceCount"]
                max_instance_count = item["maxInstanceCount"]

                if "osType" in item:
                    os_type = item["osType"]
                if "publisherId" in item:
                    publisher_id = item["publisherId"]
                if "offerId" in item:
                    offer_id = item["offerId"]
                if "planId" in item:
                    plan_id = item["planId"]
                if "meterId" in item:
                    meter_id = item["meterId"]
                if "partNumber" in item:
                    part_number = item["partNumber"]

                rows.append(
                    [
                        base_image,
                        cores_per_instance,
                        memory_in_gb_per_instance,
                        start_instance_count,
                        max_instance_count,
                        os_type,
                        publisher_id,
                        offer_id,
                        plan_id,
                        meter_id,
                        part_number,
                    ]
                )

                dict_rows.append(
                    {
                        "baseImage": base_image,
                        "defaultCoresPerInstance": cores_per_instance,
                        "defaultMemoryInGBPerInstance": memory_in_gb_per_instance,
                        "defaultStartInstanceCount": start_instance_count,
                        "defaultMaxInstanceCount": max_instance_count,
                        "osType": os_type,
                        "publisherId": publisher_id,
                        "offerId": offer_id,
                        "planId": plan_id,
                        "meterId": meter_id,
                        "partNumber": part_number,
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
                    "Default Max Instance Count",
                    "OS Type",
                    "Publisher Id",
                    "Offer Id",
                    "Plan Id",
                    "Meter Id",
                    "Part Number",
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
