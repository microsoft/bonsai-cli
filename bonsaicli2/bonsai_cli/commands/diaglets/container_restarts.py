import os
from typing import Any, Dict, Tuple
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import ContainerGroup
from azure.identity import DefaultAzureCredential

from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
import csv


class ContainerRestartsDiaglet(Diaglet):
    """
    Looks up the details of the containers running for brain training to see if there have been
    any restarts - a common symptom for problematic simulators
    """

    friendly_name = "Managed Simulator Restarts"

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        super(ContainerRestartsDiaglet, self).__init__(diagnostic_configuration)

    def diagnose(self):

        if self.diagnostic_configuration.is_test:
            self.message = "Automated CLI tests do not use managed simulators"
            return

        # assume the best to start
        self.message: str = "There are no simulator restarts."

        # Acquire a credential object
        credential = DefaultAzureCredential()

        # https://docs.microsoft.com/en-us/python/api/azure-mgmt-containerinstance/azure.mgmt.containerinstance.containerinstancemanagementclient?view=azure-python
        aci_client: ContainerInstanceManagementClient = (
            ContainerInstanceManagementClient(
                credential, self.diagnostic_configuration.subscription_id
            )
        )

        # list the container groups that are running
        container_groups = aci_client.container_groups.list_by_resource_group(
            self.diagnostic_configuration.managed_resource_group_name
        )

        problematic_groups: Dict[str, Tuple[int, int]] = {}

        container_filter = self.get_container_group_name()

        for container_group in container_groups:

            # only get the details for the brain and version we care about
            if container_filter in container_group.name:
                # get the details of the container group - includes the instance view
                cg: ContainerGroup = aci_client.container_groups.get(
                    container_group_name=container_group.name,
                    resource_group_name=self.diagnostic_configuration.managed_resource_group_name,
                )

                restart_count: int = 0

                # add up the restarts across instances
                for container in cg.containers:
                    if container.instance_view is not None:
                        restart_count += container.instance_view.restart_count

                # if there are restarts, track the name, number of total restarts and number of container instances running
                if restart_count > 0:
                    problematic_groups[container_group.name] = (
                        restart_count,
                        len(cg.containers),
                    )

        total_restarts = 0
        total_instances = 0

        file: str = self.__class__.__name__

        file: str = os.path.join(
            self.diagnostic_configuration.log_path,
            self.diagnostic_configuration.unique_name,
            f"{file}.csv",
        )

        header: list[str] = ["ContainerGroup", "Restarts"]

        with open(file, "w", encoding="UTF8", newline="") as f:
            writer = csv.writer(f)

            # write the header
            writer.writerow(header)

            # format the error message
            for cg_name in problematic_groups.keys():
                details = problematic_groups[cg_name]
                total_restarts += details[0]
                total_instances += details[1]

                data: list[Any] = [cg_name, details[0]]
                writer.writerow(data)

            # if the message needs to change, set accordingly
            if total_restarts > 0 and total_instances > 0:
                self.message = "\n".join(
                    [
                        f"There are {total_restarts} restarts across {total_instances} simulator instances.",
                        "This is commonly due to errors during simulator execution.",
                        "See https://docs.microsoft.com/bonsai/ui/sim-restart to learn about common causes and remedies for restarts.",
                    ]
                )
            elif total_instances > 0:
                self.message = f"There are 0 restarts across {total_instances} simulator instances."
