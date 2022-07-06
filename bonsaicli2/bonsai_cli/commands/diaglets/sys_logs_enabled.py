import pandas as pd
from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration


class SysLogsEnabledDiaglet(Diaglet):
    """
    Checks the managed simulator logs are enabled
    """

    friendly_name = "Managed Simulator Logging Check"

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        super(SysLogsEnabledDiaglet, self).__init__(diagnostic_configuration)

    def diagnose(self):

        kql_query = "\n".join(
            [
                "ContainerInstanceLog_CL",
                f'| where ContainerGroup_s contains "{self.get_container_group_name()}"',
                "| order by TimeGenerated desc" "| limit 1",
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
            self.message = f"There are no simulator logs. See https://docs.microsoft.com/en-us/bonsai/guides/sim-logging for how to enable logs."
            self.break_the_chain = True
        else:
            self.message = f"Simulator logging is enabled. Continuing."
