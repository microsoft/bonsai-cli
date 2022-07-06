import pandas as pd
from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration


class SDKVersionDiaglet(Diaglet):
    """
    Checks the SDK version
    """

    friendly_name = "SDK Version Check"

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        super(SDKVersionDiaglet, self).__init__(diagnostic_configuration)

    def diagnose(self):

        kql_query = "\n".join(
            [
                "ContainerInstanceLog_CL",
                f'| where ContainerGroup_s contains "{self.get_container_group_name()}"',
                '| where Message contains "microsoft-bonsai-api" and Message contains "version"',
                "| project Message",
                "| limit 1",
            ]
        )

        timespan = timedelta(days=30)

        if self.diagnostic_configuration.is_test:
            # Create a Python list of dictionaries
            data = [{"Message": "This is an automated test"}]
            df = pd.DataFrame(data)
        else:
            df, _ = self.run_kql_query(kql_query, timespan)

        if len(df) == 1:
            # just print what the message says
            self.message = df.iloc[0]["Message"]
        else:
            self.message = f"Could not retrieve SDK version details."
