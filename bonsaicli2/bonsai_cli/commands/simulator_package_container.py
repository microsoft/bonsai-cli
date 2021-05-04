"""
This file contains the code for commands that target a bonsai container simulator package in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2021, Microsoft Corp."

import click
import math

from json import dumps

from bonsai_cli.exceptions import AuthenticationError, BrainServerError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_client_side_click_exception,
    raise_unique_constraint_violation_as_click_exception,
)


@click.group()
def container():
    """Container simulator package operations."""
    pass


@click.command("create", short_help="Create a container simulator package.")
@click.option(
    "--name", "-n", help="[Required] Name of the container simulator package."
)
@click.option(
    "--image-uri",
    "-u",
    help="[Required] URI of the container simulator package (container).",
)
@click.option(
    "--cores-per-instance",
    "-r",
    type=float,
    help="[Required] Number of cores that should be allocated for each simulator instance.",
)
@click.option(
    "--memory-in-gb-per-instance",
    "-m",
    type=float,
    help="[Required] Memory in GB that should be allocated for each simulator instance.",
)
@click.option(
    "--os-type",
    "-p",
    help="[Required] OS type for the container simulator package. Windows or Linux.",
    type=click.Choice(["Windows", "Linux"], case_sensitive=False),
)
@click.option(
    "--instance-count",
    "-i",
    type=int,
    help="Number of instances to start and perform training with the container simulator package.",
)
@click.option(
    "--min-instance-count",
    type=int,
    help="Minimum Number of instances to perform training with the container simulator package.",
)
@click.option(
    "--max-instance-count",
    type=int,
    help="Maximum Number of instances to perform training with the container simulator package.",
)
@click.option(
    "--auto-scale",
    type=bool,
    help="Flag to indicate scale up or scale down simulators. By default, it is set to true",
    default=True,
)
@click.option("--display-name", help="Display name of the container simulator package.")
@click.option("--description", help="Description for the container simulator package.")
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
def create_container_simulator_package(
    ctx: click.Context,
    name: str,
    image_uri: str,
    instance_count: int,
    min_instance_count: int,
    max_instance_count: int,
    cores_per_instance: float,
    memory_in_gb_per_instance: float,
    auto_scale: bool,
    os_type: str,
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
        error_msg += "\nName of the container simulator package is required"

    if not image_uri:
        required_options_provided = False
        error_msg += "\nUri for the container simulator package is required"

    if not cores_per_instance:
        required_options_provided = False
        error_msg += "\nCores per instance for the simulator is required"

    if not memory_in_gb_per_instance:
        required_options_provided = False
        error_msg += "\nMemory in GB per instance for the simulator is required"

    if not os_type:
        required_options_provided = False
        error_msg += "\nOS type for the container simulator package is required"

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    # if autoscale is true, max_instance_count is mandatory and min instance count and max instance count must be greater than one.
    # min instance count and start instance count, if not defined is set to max instance count divide by 4.(as per Product Requirement.)

    # if autoscale is set to false, start_instance_count is mandatory and min_instance_count and max_instance_count must be set to start_instance_count

    if auto_scale:
        if not max_instance_count:
            error_msg += "\nIf auto scale is true, maximum instance count(--max-instance-count) is required."
            raise_as_click_exception(error_msg)

        # if min_instance_count is less than 1, set it to minimum 1.
        if not min_instance_count:
            min_instance_count = max(math.floor(max_instance_count / 4), 1)

        # if instance_count is less than 1, set it to minimum 1.
        if not instance_count:
            instance_count = max(math.floor(max_instance_count / 4), 1)
    else:
        if not instance_count:
            error_msg += "\nIf auto scale is set to false, instance count(--instance-count) is required."
            raise_as_click_exception(error_msg)

        if min_instance_count or max_instance_count:
            error_msg += "\nMinimum instance count(--min-instance-count) and maximum instance count(--max-instance-count) cannot be provided as an option in case of auto scale being set to false. Minimum instance count and maximum instance count will be internally set to the same value as start instance count(--instance-count)."
            raise_as_click_exception(error_msg)

        min_instance_count = max_instance_count = instance_count

    # Range Validation for max count and start instance count

    if max_instance_count < min_instance_count or max_instance_count < instance_count:
        error_msg += "\nMaximum instance count(--max-instance-count) must be greater than or equal to minimum instance count(--min-instance-count) and instance count(--instance-count)."
        raise_as_click_exception(error_msg)

    if instance_count < min_instance_count:
        error_msg += "\nInstance count(--instance-count) must be greater than or equal to minimum instance count(--min-instance-count). If not explicitly set, Instance count(--instance-count) by default is 0."
        raise_as_click_exception(error_msg)

    try:
        response = api(use_aad=True).create_sim_package(
            name=name,
            image_path=image_uri,
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
            os_type=os_type,
            package_type="container",
            workspace=workspace_id,
            debug=debug,
            output=output,
        )

        status_message = "Created new container simulator package {}.".format(
            response["name"]
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
        if "Unique index constraint violation" in str(e):
            raise_unique_constraint_violation_as_click_exception(
                debug, output, "Container simulator package", name, test, e
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


container.add_command(create_container_simulator_package)
