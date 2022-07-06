import os
from typing import Any, Tuple
import pandas as pd

from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.monitor.query._models import LogsTable
from bonsai_cli.utils import api


class Diaglet:
    """
    Base class for all diaglets
    """

    friendly_name: str = ""
    """
    provide a friendly name for the diaglet
    """

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        self.diagnostic_configuration: DiagletConfiguration = diagnostic_configuration
        """
        contains the workspace, subscription and brain details to check diagnostics against 
        """

        self.message: str = ""
        """
        the message displayed by the diaglet
        """

        self.client: LogsQueryClient = LogsQueryClient(DefaultAzureCredential())
        """
        the client for working with Log Analytics
        """

        self.break_the_chain: bool = False
        """
        indicates if no other processing should occur after this diaglet runs
        """

    def diagnose(self) -> None:
        """
        performs diagnostics using this diaglet
        """
        pass

    def run_kql_query(
        self, query: str, timespan: timedelta
    ) -> Tuple[pd.DataFrame, str]:
        """
        runs a KQL query for the given timespan
        """
        response = self.client.query_workspace(
            workspace_id=self.diagnostic_configuration.log_analytics_workspace_id,
            query=query,
            timespan=timespan,
        )

        data: list[LogsTable] = []

        if response.status == LogsQueryStatus.PARTIAL:
            error = response.partial_error
            data = response.partial_data
            self.message = error.message
        elif response.status == LogsQueryStatus.SUCCESS:
            data = response.tables

        df: Any = pd.DataFrame(data=data[0].rows, columns=data[0].columns)
        df = df.drop_duplicates()
        df = df.reset_index(drop=True)

        file: str = self.__class__.__name__

        # save the query results to a CSV file to include in any Bonsai team communication
        file: str = os.path.join(
            self.diagnostic_configuration.log_path,
            self.diagnostic_configuration.unique_name,
            f"{file}.csv",
        )

        if not self.diagnostic_configuration.is_test:
            df.to_csv(file)

        return (df, file)

    def get_container_group_name(self) -> str:
        """
        gets the container instance name to use as a filter
        """

        try:
            # call the Bonsai API to get brain version details
            response: Any = api(use_aad=True).get_brain_version(
                name=self.diagnostic_configuration.brain_name,
                version=self.diagnostic_configuration.brain_version,
                workspace=self.diagnostic_configuration.workspace_id,
            )

            brain_version_id: str = response["id"]
            concept_id: str = ""

            for c in response["concepts"]:
                if c["name"] == self.diagnostic_configuration.concept_name:
                    concept_id = c["id"]

            # some single concept brains are empty or are brain_version_id/concept name -- ignore those
            if len(concept_id) == 0 or len(concept_id) > 36:
                return brain_version_id
            else:
                return f"{brain_version_id}_{concept_id}"
        except:
            print(
                f"Could not find details for {self.diagnostic_configuration.workspace_id}/{self.diagnostic_configuration.brain_name}/{self.diagnostic_configuration.brain_version}"
            )
            exit()
