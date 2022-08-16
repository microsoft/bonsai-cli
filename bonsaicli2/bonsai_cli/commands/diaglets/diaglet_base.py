import os
from typing import Any, Dict, List, Tuple
import sys
import platform
import subprocess

from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration
from azure.core.exceptions import HttpResponseError
from azure.identity import (
    ChainedTokenCredential,
    DeviceCodeCredential,
    AzureCliCredential,
    SharedTokenCacheCredential,
    TokenCachePersistenceOptions,
)
from azure.core.credentials import TokenCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.monitor.query._models import LogsTable
from bonsai_cli.utils import api, raise_as_click_exception


class Diaglet:
    """
    Base class for all diaglets
    """

    credential: Any = None

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

        self.client: Any = None
        """
        the client for working with Log Analytics
        """

        self.break_the_chain: bool = False
        """
        indicates if no other processing should occur after this diaglet runs
        """

        self.pandas_error_message = "Cannot import pandas. This is likely due to not having bzip installed on this machine. pandas is required to execute most diagnose commands."
        """
        the error message to display when pandas is not available
        """

    def diagnose(self) -> None:
        """
        performs diagnostics using this diaglet
        """
        pass

    def run_kql_query(self, query: str, timespan: timedelta) -> Tuple[Any, str]:
        """
        runs a KQL query for the given timespan
        """
        try:
            # some Python environments aren't installed with bzip, so test if can import pandas
            import pandas

            try:
                if self.client is None:
                    self.client = LogsQueryClient(self.acquire_token_credential())

                with self.client:
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

                    df: Any = pandas.DataFrame(
                        data=data[0].rows, columns=data[0].columns
                    )
                    df = df.drop_duplicates()
                    df = df.reset_index(drop=True)

            except HttpResponseError as e:
                # set an empty dataframe
                df: Any = pandas.DataFrame()

                # if the user has never enabled logging, they get an error the table cannot be found
                if "Failed to resolve table" not in e.message:
                    print(e)

            file: str = (
                self.__class__.__name__
                + "_"
                + self.diagnostic_configuration.concept_name
            )

            # save the query results to a CSV file to include in any Bonsai team communication
            file: str = os.path.join(
                self.diagnostic_configuration.log_path,
                self.diagnostic_configuration.unique_name,
                f"{file}.csv",
            )

            if not self.diagnostic_configuration.is_test:
                df.to_csv(file)

            return (df, file)

        except:
            raise_as_click_exception(self.pandas_error_message)

    def get_test_dataframe(self, data: List[Dict[str, Any]]):
        try:
            # some Python environments aren't installed with bzip, so test if can import pandas
            import pandas

            return pandas.DataFrame(data)
        except:
            raise_as_click_exception(self.pandas_error_message)

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
                if (
                    c["name"].lower()
                    == self.diagnostic_configuration.concept_name.lower()
                ):
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

    def acquire_token_credential(self) -> TokenCredential:
        """
        retrieves the credential used to connect to other services
        """

        # use a cached credential if possible
        if Diaglet.credential is not None:
            return Diaglet.credential

        chained_credential: Any = None

        try:
            command = "az account list"

            if sys.platform.startswith("win"):
                args = ["cmd", "/c", command]
            else:
                args = ["/bin/sh", "-c", command]

            working_directory = self.get_safe_working_dir()

            kwargs = {
                "stderr": subprocess.STDOUT,
                "cwd": working_directory,
                "universal_newlines": True,
                "env": dict(os.environ, AZURE_CORE_NO_COLOR="true"),
            }
            if platform.python_version() >= "3.3":
                kwargs["timeout"] = 10

            subprocess.check_output(args, **kwargs)

            chained_credential = ChainedTokenCredential(
                SharedTokenCacheCredential(),
                AzureCliCredential(),
                DeviceCodeCredential(
                    cache_persistence_options=TokenCachePersistenceOptions(
                        allow_unencrypted_storage=True
                    )
                ),
            )
        except:
            chained_credential = ChainedTokenCredential(
                SharedTokenCacheCredential(),
                DeviceCodeCredential(
                    cache_persistence_options=TokenCachePersistenceOptions(
                        allow_unencrypted_storage=True
                    )
                ),
            )

        Diaglet.credential = chained_credential

        return Diaglet.credential

    def get_safe_working_dir(self):
        """Invoke 'az' from a directory controlled by the OS, not the executing program's directory"""

        if sys.platform.startswith("win"):
            path = os.environ.get("SYSTEMROOT")
            if not path:
                raise Exception("Environment variable 'SYSTEMROOT' has no value")
            return path

        return "/bin"
