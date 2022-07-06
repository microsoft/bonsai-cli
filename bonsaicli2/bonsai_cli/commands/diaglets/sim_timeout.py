import pandas as pd
from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration


class SimTimeoutDiaglet(Diaglet):
    """
    Checks the managed simulator logs for timeout errors
    """

    friendly_name = "Managed Simulator Timeouts"

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        super(SimTimeoutDiaglet, self).__init__(diagnostic_configuration)

    def diagnose(self):

        kql_query = "\n".join(
            [
                "ContainerInstanceLog_CL",
                f'| where ContainerGroup_s contains "{self.get_container_group_name()}"',
                '| where Message contains "Simulator timed out"',
            ]
        )

        timespan = timedelta(days=30)

        if self.diagnostic_configuration.is_test:
            # Create a Python list of dictionaries
            data = [{"Message": "This is an automated test"}]
            df = pd.DataFrame(data)
        else:
            df, _ = self.run_kql_query(kql_query, timespan)

        if len(df) == 0:
            self.message = f"There are no simulator timeouts."
        else:
            self.message = f"There are {len(df)} simulator timeouts. See https://docs.microsoft.com/en-us/bonsai/troubleshoot/managed-sims/timeout to learn about common causes and remedies for timeouts."
