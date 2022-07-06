import pandas as pd
from pandas import DataFrame
from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration


class EpisodeLogsEnabledDiaglet(Diaglet):
    """
    Checks the episode logs are enabled
    """

    friendly_name = "Episode Logging Check"

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        super(EpisodeLogsEnabledDiaglet, self).__init__(diagnostic_configuration)

    def diagnose(self):

        kql_query = "\n".join(
            [
                "EpisodeLog_CL",
                f'| where BrainName_s=="{self.diagnostic_configuration.brain_name}"',
                f"| where BrainVersion_d=={self.diagnostic_configuration.brain_version}",
                "| limit 1",
            ]
        )

        timespan = timedelta(days=30)

        if self.diagnostic_configuration.is_test:
            # Create a Python list of dictionaries
            data = [{"RecordA": "Dummy", "RecordB": 404, "RecordC": "Test"}]
            df: DataFrame = pd.DataFrame(data)
        else:
            df, _ = self.run_kql_query(kql_query, timespan)

        if len(df) == 0:
            self.message = f"There are no episode logs. See https://docs.microsoft.com/en-us/bonsai/guides/sim-logging for how to enable episode logs."
            self.break_the_chain = True
        else:
            self.message = f"Episode logging is enabled. Continuing."
