import pandas as pd
from datetime import timedelta
from bonsai_cli.commands.diaglets.diaglet_base import Diaglet
from bonsai_cli.commands.diaglets.diaglet_configuration import DiagletConfiguration


class IterationHaltedDiaglet(Diaglet):
    """
    Checks the iteration logs for halted information
    """

    friendly_name = "Iteration Halted Check"

    def __init__(self, diagnostic_configuration: DiagletConfiguration):
        super(IterationHaltedDiaglet, self).__init__(diagnostic_configuration)

    def diagnose(self):

        kql_query = "\n".join(
            [
                "IterationLog_CL",
                f'| where BrainName_s=="{self.diagnostic_configuration.brain_name}"',
                f"| where BrainVersion_d=={self.diagnostic_configuration.brain_version}",
                f"| where Halted_b==true" "| limit 1000",
            ]
        )

        timespan = timedelta(days=30)

        if self.diagnostic_configuration.is_test:
            # Create a Python list of dictionaries
            data = [{"RecordA": "Dummy", "RecordB": 404, "RecordC": "Test"}]
            df = pd.DataFrame(data)
        else:
            df, _ = self.run_kql_query(kql_query, timespan)

        if len(df) == 0:
            self.message = f"There are no halted iterations."
        else:
            self.message = "\n".join(
                [
                    f"There are {len(df)} halted iterations.",
                    "Halted iterations may impact brain training if not used with an avoid goal in inkling.",
                    "See https://docs.microsoft.com/bonsai/ui/sim-halted to learn about common causes and remedies for halted conditions.",
                ]
            )
