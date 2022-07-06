"""
This file contains the code for commands that target a deploying a bonsai exported brain in version 2 of the bonsai command line.
"""
__author__ = "David Coe"
__copyright__ = "Copyright 2022, Microsoft Corp."

import click
import os
import shutil
from datetime import datetime


from bonsai_cli.utils import (
    api,
    get_version_checker,
    raise_as_click_exception,
)

from .brain_version import get_latest_brain_version

# import the diaglets
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration
from bonsai_cli.commands.diaglets.container_restarts import ContainerRestartsDiaglet
from bonsai_cli.commands.diaglets.error_messages import ErrorsDiaglet
from bonsai_cli.commands.diaglets.episode_logs_enabled import EpisodeLogsEnabledDiaglet
from bonsai_cli.commands.diaglets.iteration_halted import IterationHaltedDiaglet
from bonsai_cli.commands.diaglets.last_n_records import LastNRecordsDiaglet
from bonsai_cli.commands.diaglets.last_n_records import LastNRecordsDiaglet
from bonsai_cli.commands.diaglets.sdk_version import SDKVersionDiaglet
from bonsai_cli.commands.diaglets.sim_timeout import SimTimeoutDiaglet
from bonsai_cli.commands.diaglets.sys_logs_enabled import SysLogsEnabledDiaglet


@click.group(hidden=True)
def diagnose():
    """
    Diagnoses a brain in various states
    """
    pass


@click.command(
    "brain", short_help="Checks the training health of a brain and its simulators."
)
@click.pass_context
@click.option("--name", "-n", help="[Required] Name of the brain.")
@click.option(
    "--version", type=int, help="Version to check training health, defaults to latest."
)
@click.option("--concept-name", "-c", help="Concept to check.")
@click.option("--output", "-o", help="Set output, only zip supported.")
@click.option(
    "--test",
    default=False,
    is_flag=True,
    help="Enhanced response for testing.",
    hidden=True,
)
def diagnose_brain(
    ctx: click.Context,
    name: str,
    version: int,
    concept_name: str,
    output: str,
    test: bool,
):
    version_checker = get_version_checker(ctx, interactive=not output)

    if not name:
        raise_as_click_exception("Name of the brain is required.")

    if not concept_name:
        raise_as_click_exception("Name of the concept is required.")

    if not version:
        version = get_latest_brain_version(name, "diagnose brain", False, "", False)

    bonsai_api = api(True)
    workspace_resources = bonsai_api.get_workspace_resources()

    diaglet_config = DiagletConfiguration()
    diaglet_config.brain_name = name
    diaglet_config.brain_version = version
    diaglet_config.concept_name = concept_name
    diaglet_config.is_test = test
    diaglet_config.unique_name = str(
        (datetime.now() - datetime(1, 1, 1)).total_seconds()
    ).replace(".", "")

    diaglet_config.workspace_id = bonsai_api.workspace_id
    diaglet_config.subscription_id = workspace_resources["subscriptionId"]
    diaglet_config.managed_resource_group_name = workspace_resources[
        "serviceProvisionedResourceGroup"
    ]
    diaglet_config.log_analytics_workspace_id = workspace_resources[
        "logAnalyticsWorkspaceId"
    ]

    log_dir: str = ""

    # dont write files during the tests
    if not test:
        if not os.path.exists(diaglet_config.log_path):
            os.makedirs(diaglet_config.log_path)

        log_dir = os.path.join(diaglet_config.log_path, diaglet_config.unique_name)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    # the chain of diaglets to run. order is important because diaglets can stop processing the chain
    diaglet_chain = [
        ContainerRestartsDiaglet(diaglet_config),
        [
            SysLogsEnabledDiaglet(diaglet_config),
            SDKVersionDiaglet(diaglet_config),
            SimTimeoutDiaglet(diaglet_config),
            ErrorsDiaglet(diaglet_config),
        ],
        [
            EpisodeLogsEnabledDiaglet(diaglet_config),
            IterationHaltedDiaglet(diaglet_config),
        ],
    ]

    print()
    print(
        f"Analyzing training diagnostics for brain {diaglet_config.brain_name}, version {diaglet_config.brain_version}:"
    )
    print()

    for diaglet in diaglet_chain:
        if isinstance(diaglet, Diaglet):
            break_chain = run_diaglet(diaglet)

            if break_chain:
                print("Cannot continue diagnostics.\n")
                break
        else:  # its a list
            for d in diaglet:
                break_segment = run_diaglet(d)

                if break_segment:
                    print("Cannot continue diagnostics in this segment.\n")
                    break

    if output == "zip":
        # also save the last N records in case the diaglets missed something
        last_n_records = LastNRecordsDiaglet(diaglet_config)
        last_n_records.diagnose()

        # zip up the files and delete the directory
        output_filename = os.path.join(
            diaglet_config.log_path, f"diagnostics_{diaglet_config.unique_name}"
        )

        shutil.make_archive(output_filename, "zip", log_dir)
        shutil.rmtree(log_dir)

        # notify the user where the files are
        print(f"All logs saved to {output_filename}.zip")

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


def run_diaglet(diaglet: Diaglet) -> bool:
    """
    runs the diaglet to get the output message and whether it should break the chain or segment it is in
    """
    diaglet.diagnose()

    print(f"{diaglet.friendly_name} -- {diaglet.message}\n")

    return diaglet.break_the_chain


diagnose.add_command(diagnose_brain)
