import os


class DiagletConfiguration:
    """
    Configuration details about the Bonsai workspace used to perform diagnostics
    """

    def __init__(self):
        self.unique_name: str = ""
        """
        provides a unique name for this run based on seconds since 1/1/1970
        """

        self.log_path: str = os.path.join(
            os.path.expanduser("~"), ".bonsai_diagnose_logs"
        )
        """
        the root path to save logs to 
        """

        self.log_analytics_workspace_id: str = ""
        """
        the Log Analytics Workspace ID (ie, not ResourceID) for working with Log Analytics
        """

        self.subscription_id: str = ""
        """
        the subscription ID to use when getting container instance details
        """

        self.managed_resource_group_name: str = ""
        """
        the name of the resource group where containers are created
        """

        self.workspace_id: str = ""
        """
        the Bonsai workspace ID
        """

        self.brain_name: str = ""
        """
        the name of the brain to diagnose
        """

        self.brain_version: int = -1
        """
        the version of the brain to diagnose
        """

        self.concept_name: str = ""
        """
        the name of the concept to diagnose
        """

        self.is_test: bool = False
        """
        indicates if this run is part of an automated test
        """
