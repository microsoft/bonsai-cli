import pandas as pd
from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration


class LastNRecordsDiaglet(Diaglet):
    """
    Pulls the last N records
    """

    friendly_name = "Pull last 1000 records"

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        super(LastNRecordsDiaglet, self).__init__(diagnostic_configuration)

    def diagnose(self):

        kql_query = "\n".join(
            [
                "ContainerInstanceLog_CL",
                f'| where ContainerGroup_s contains "{self.get_container_group_name()}"',
                "| order by TimeGenerated desc",
                "| limit 1000",
            ]
        )

        timespan = timedelta(days=30)

        if self.diagnostic_configuration.is_test:
            # Create a Python list of dictionaries
            data = [{"RecordA": "Dummy", "RecordB": 404, "RecordC": "Test"}]
            df = pd.DataFrame(data)
        else:
            df, _ = self.run_kql_query(kql_query, timespan)

        self.message = f"Saved the last {len(df)} records."
