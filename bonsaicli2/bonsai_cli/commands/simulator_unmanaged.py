"""
This file contains the code for commands that target a bonsai unmanaged simulator in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

import click
from json import dumps
from tabulate import tabulate

from bonsai_cli.api import BrainServerError
from bonsai_cli.exceptions import AuthenticationError
from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
    raise_brain_server_error_as_click_exception,
    raise_not_found_as_click_exception,
)
from .brain_version import get_latest_brain_version


@click.group()
def unmanaged():
    """Unmanaged simulator operations."""
    pass


@click.command("list", short_help="Lists unmanaged simulators owned by current user.")
@click.option("--simulator-name", help="Filter by simulator name.")
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
def list_simulator_unmanaged(
    ctx: click.Context,
    simulator_name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    try:
        response = api(use_aad=True).list_unmanaged_sim_session(
            workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    rows = []
    dict_rows = []
    if simulator_name:
        for item in response["value"]:
            try:
                if item["simulatorName"] == simulator_name:
                    name = item["simulatorName"]
                    session_id = item["sessionId"]
                    action = "Unset"
                    target_brain_name = "-"
                    target_brain_version = "-"
                    target_concept = "-"

                    if (
                        item["simulatorContext"]["purpose"]["action"] == "Train"
                        or item["simulatorContext"]["purpose"]["action"] == "Assess"
                    ):
                        action = item["simulatorContext"]["purpose"]["action"]
                        target_brain_name = item["simulatorContext"]["purpose"][
                            "target"
                        ]["brainName"]
                        target_brain_version = item["simulatorContext"]["purpose"][
                            "target"
                        ]["brainVersion"]
                        target_concept = item["simulatorContext"]["purpose"]["target"][
                            "conceptName"
                        ]

                    rows.append(
                        [
                            name,
                            session_id,
                            action,
                            target_brain_name,
                            target_brain_version,
                            target_concept,
                        ]
                    )
                    dict_rows.append(
                        {
                            "name": name,
                            "sessionId": session_id,
                            "action": action,
                            "targetBrainName": target_brain_name,
                            "targetBrainVersion": target_brain_version,
                            "targetConcept": target_concept,
                        }
                    )
            except KeyError:
                pass  # If it's missing a field, ignore it.

        if len(rows) == 0:
            click.echo(
                "No unmanaged simulators with simulator name {} exist for the current user".format(
                    simulator_name
                )
            )
            ctx.exit()

    else:
        for item in response["value"]:
            try:
                name = item["simulatorName"]
                session_id = item["sessionId"]
                action = "Unset"
                target_brain_name = "-"
                target_brain_version = "-"
                target_concept = "-"

                if (
                    item["simulatorContext"]["purpose"]["action"] == "Train"
                    or item["simulatorContext"]["purpose"]["action"] == "Assess"
                ):
                    action = item["simulatorContext"]["purpose"]["action"]
                    target_brain_name = item["simulatorContext"]["purpose"]["target"][
                        "brainName"
                    ]
                    target_brain_version = item["simulatorContext"]["purpose"][
                        "target"
                    ]["brainVersion"]
                    target_concept = item["simulatorContext"]["purpose"]["target"][
                        "conceptName"
                    ]

                rows.append(
                    [
                        name,
                        session_id,
                        action,
                        target_brain_name,
                        target_brain_version,
                        target_concept,
                    ]
                )
                dict_rows.append(
                    {
                        "name": name,
                        "sessionId": session_id,
                        "action": action,
                        "targetBrainName": target_brain_name,
                        "targetBrainVersion": target_brain_version,
                        "targetConcept": target_concept,
                    }
                )
            except KeyError:
                pass  # If it's missing a field, ignore it.

            if len(rows) == 0:
                click.echo("No unmanaged simulators exist for the current user")
                ctx.exit()

    if output == "json":
        json_response = {
            "value": dict_rows,
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": "",
        }

        click.echo(dumps(json_response, indent=4))

    else:
        table = tabulate(
            rows,
            headers=[
                "Name",
                "Session Id",
                "Action",
                "Target Brain Name",
                "Target Brain Version",
                "Target Concept",
            ],
            tablefmt="orgtbl",
        )
        click.echo(table)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("show", short_help="Show information about an unmanaged simulator.")
@click.option(
    "--session-id", "-d", help="[Required] Identifier for the unmanaged simulator."
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
def show_simulator_unmanaged(
    ctx: click.Context,
    session_id: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    if not session_id:
        raise_as_click_exception("\nIdentifier for the unmanaged simulator is required")

    try:
        response = api(use_aad=True).get_sim_session(
            session_id, workspace=workspace_id, debug=debug, output=output
        )

    except BrainServerError as e:
        if e.exception["statusCode"] == 404:
            raise_not_found_as_click_exception(
                debug,
                output,
                "Show simulator unmanaged",
                "Simulator unmanaged",
                session_id,
                test,
                e,
            )
        else:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

    except AuthenticationError as e:
        raise_as_click_exception(e)

    action = "Unset"
    target_brain_name = "-"
    target_brain_version = "-"
    target_concept = "-"

    if (
        response["simulatorContext"]["purpose"]["action"] == "Train"
        or response["simulatorContext"]["purpose"]["action"] == "Assess"
    ):
        action = response["simulatorContext"]["purpose"]["action"]
        target_brain_name = response["simulatorContext"]["purpose"]["target"][
            "brainName"
        ]
        target_brain_version = response["simulatorContext"]["purpose"]["target"][
            "brainVersion"
        ]
        target_concept = response["simulatorContext"]["purpose"]["target"][
            "conceptName"
        ]

    if output == "json":
        json_response = {
            "status": response["status"],
            "statusCode": response["statusCode"],
            "statusMessage": {
                "name": response["interface"]["name"],
                "action": action,
                "targetBrainName": target_brain_name,
                "targetBrainVersion": target_brain_version,
                "targetConcept": target_concept,
            },
        }

        click.echo(dumps(json_response, indent=4))

    else:
        click.echo("Name: {}".format(response["interface"]["name"]))
        click.echo("Action: {}".format(action))
        click.echo("Target Brain Name: {}".format(target_brain_name))
        click.echo("Target Brain Version: {}".format(target_brain_version))
        click.echo("Target Concept: {}".format(target_concept))

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("connect", short_help="Connect an unmanaged simulator.")
@click.option(
    "--brain-name",
    "-b",
    help="[Required] The name of the brain for the simulators to connect to.",
)
@click.option(
    "--action", "-a", help="[Required] The assigned action for the simulators."
)
@click.option(
    "--concept-name",
    "-c",
    help="[Required] The name of the concept for the simulators to connect to.",
)
@click.option(
    "--brain-version",
    type=int,
    help="The version of the brain for the simulators to connect to, defaults to latest.",
)
@click.option("--session-id", "-d", help="Identifier for the simulator.")
@click.option(
    "--simulator-name",
    help="The name of the simulator, provide this if you would like to connect all simulators with this name.",
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
def connect_simulator_unmanaged(
    ctx: click.Context,
    session_id: str,
    brain_name: str,
    brain_version: int,
    action: str,
    concept_name: str,
    simulator_name: str,
    workspace_id: str,
    debug: bool,
    output: str,
    test: bool,
):

    version_checker = get_version_checker(ctx, interactive=not output)

    error_msg = ""
    required_options_provided = True

    if not brain_name:
        required_options_provided = False
        error_msg += "\nBrain name is required"

    if not action:
        required_options_provided = False
        error_msg += "\nAction is required"

    if not concept_name:
        required_options_provided = False
        error_msg += "\nConcept name is required"

    if session_id and simulator_name:
        required_options_provided = False
        error_msg += "\nPlease provide either session id or simulator name but not both"

    if not session_id and not simulator_name:
        required_options_provided = False
        error_msg += "\nPlease provide either session id or simulator name"

    if not required_options_provided:
        raise_as_click_exception(error_msg)

    if not brain_version:
        brain_version = get_latest_brain_version(
            brain_name, "Connect simulator unmanaged", debug, output, test
        )

    action = action.capitalize()

    if simulator_name:
        try:
            response = api(use_aad=True).list_unmanaged_sim_session(
                workspace=workspace_id, debug=False, output=output
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        total_simulators = 0

        inactive_simulators = 0
        active = 0
        failure_status_code = 500

        for sim in response["value"]:
            if sim["simulatorName"] == simulator_name:
                total_simulators += 1

                if (
                    sim["simulatorContext"]["purpose"]["action"] == "Train"
                    or sim["simulatorContext"]["purpose"]["action"] == "Assess"
                ):
                    active += 1

                if sim["simulatorContext"]["purpose"]["action"] == "Inactive":
                    try:
                        api(use_aad=True).patch_sim_session(
                            session_id=sim["sessionId"],
                            brain_name=brain_name,
                            version=brain_version,
                            purpose_action=action,
                            concept_name=concept_name,
                            workspace=workspace_id,
                            debug=debug,
                            output=output,
                        )

                        active += 1

                    except BrainServerError as e:
                        if inactive_simulators == 0:
                            failure_status_code: int = e.exception["statusCode"]
                        inactive_simulators += 1

        if output == "json":
            status_message = {
                "simulatorsFound": total_simulators,
                "simulatorsConnected": active,
                "simulatorsNotConnected": inactive_simulators,
            }

            if inactive_simulators > 0:
                json_response = {
                    "status": "Failed",
                    "statusCode": failure_status_code,
                    "statusMessage": status_message,
                }
            else:
                json_response = {
                    "status": "Succeeded",
                    "statusCode": 200,
                    "statusMessage": status_message,
                }

            click.echo(dumps(json_response, indent=4))
        else:
            click.echo("Simulators Found: {}".format(total_simulators))
            click.echo("Simulators Connected: {}".format(active))
            click.echo("Simulators Not Connected: {}".format(inactive_simulators))

    else:
        try:
            show_sim_session_response = api(use_aad=True).get_sim_session(
                session_id=session_id,
                workspace=workspace_id,
                debug=debug,
                output=output,
            )

        except BrainServerError as e:
            if e.exception["statusCode"] == 404:
                raise_not_found_as_click_exception(
                    debug,
                    output,
                    "Connect simulator unmanaged",
                    "Simulator unmanaged",
                    session_id,
                    test,
                    e,
                )
            else:
                raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        if (
            show_sim_session_response["simulatorContext"]["purpose"]["action"]
            == "Train"
            or show_sim_session_response["simulatorContext"]["purpose"]["action"]
            == "Assess"
        ):
            raise_as_click_exception(
                "Unmanaged simulator with session id {} is already connected to brain {} version {} with action {}".format(
                    session_id,
                    show_sim_session_response["simulatorContext"]["purpose"]["target"][
                        "brainName"
                    ],
                    show_sim_session_response["simulatorContext"]["purpose"]["target"][
                        "brainVersion"
                    ],
                    show_sim_session_response["simulatorContext"]["purpose"]["action"],
                )
            )

        try:
            response = api(use_aad=True).patch_sim_session(
                session_id=session_id,
                brain_name=brain_name,
                version=brain_version,
                purpose_action=action,
                concept_name=concept_name,
                workspace=workspace_id,
                debug=debug,
                output=output,
            )

        except BrainServerError as e:
            raise_brain_server_error_as_click_exception(debug, output, test, e)

        except AuthenticationError as e:
            raise_as_click_exception(e)

        status_message = "{} set to {} on brain {} version {}. ".format(
            session_id, action, brain_name, brain_version
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


unmanaged.add_command(connect_simulator_unmanaged)
unmanaged.add_command(list_simulator_unmanaged)
unmanaged.add_command(show_simulator_unmanaged)
