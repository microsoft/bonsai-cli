import pandas as pd
from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration


class ErrorsDiaglet(Diaglet):
    """
    Checks for the existance of errors or exceptions in the logs
    """

    friendly_name = "Error Check"

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        super(ErrorsDiaglet, self).__init__(diagnostic_configuration)

    def diagnose(self):

        kql_query = "\n".join(
            [
                "ContainerInstanceLog_CL",
                f'| where ContainerGroup_s contains "{self.get_container_group_name()}"',
                '| where Message contains "error" or Message contains "exception"',
                "| project TimeGenerated, Message",
                "| order by TimeGenerated desc",
            ]
        )

        timespan = timedelta(days=30)

        if self.diagnostic_configuration.is_test:
            # Create a Python list of dictionaries
            data = [{"RecordA": "Dummy", "RecordB": 404, "RecordC": "Test"}]
            df = pd.DataFrame(data)
            file = "test_not_found.csv"
        else:
            df, file = self.run_kql_query(kql_query, timespan)

        if len(df) > 0:
            # just print what the message says
            self.message = f'There are {len(df)} errors or exceptions in the logs. See the log file in "{file}" for details.'
        else:
            self.message = "No errors or exceptions found in the logs."
