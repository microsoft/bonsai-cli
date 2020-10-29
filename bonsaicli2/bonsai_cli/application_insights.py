import abc
import logging

from datetime import datetime, timedelta
from opencensus.ext.azure.log_exporter import AzureEventHandler
from typing import Any, Dict

from .logger import Logger
from . import __version__

console_logger = Logger()
appInsightsLogger = logging.Logger(__name__)
appInsightsLogger.addHandler(
    AzureEventHandler(
        connection_string="InstrumentationKey=1b54b5e5-a4de-47f6-95f8-c4bb974c89b7;IngestionEndpoint=https://westus2-1.in.applicationinsights.azure.com/"
    )
)


class CustomEventInterface(metaclass=abc.ABCMeta):
    """
    This is an Abstract Class for an ApplicationInsights CustomEvent.
    """

    @abc.abstractmethod
    def upload_event(self, api_response: Dict[str, str], debug: bool) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def update_properties(self, update_dict: Dict[str, Any]) -> None:
        raise NotImplementedError


class ApplicationInsightsHandlerInterface(metaclass=abc.ABCMeta):
    """
    This is an Abstract Class for a handler of ApplicationInsights CustomEvents.
    """

    @abc.abstractmethod
    def create_event(self, event_name: str, **kwargs: Any) -> CustomEventInterface:
        raise NotImplementedError


class SkeletonCustomEvent(CustomEventInterface):
    """
    This is essentially a no-op handler. It will return a SkeletonCustomEvent,
    where the methods have no operations.
    """

    def upload_event(self, api_response: Dict[str, str], debug: bool):
        pass

    def update_properties(self, update_dict: Dict[str, Any]):
        pass


class SkeletonApplicationInsightsHandler(ApplicationInsightsHandlerInterface):
    """
    This is essentially a no-op handler. It will return a SkeletonCustomEvent,
    where the methods have no operations. If the user has opted out of
    uploading ApplicationInsights events, this allows us to keep the client calls
    in place with no changes, but also no real operations.
    """

    def create_event(self, event_name: str, **kwargs: Any) -> CustomEventInterface:
        return SkeletonCustomEvent()


class CustomEvent(CustomEventInterface):
    """
    This class represents an individual ApplicationInsights CustomEvent.
    During Initialization, set the start time of the event to the current time and include all
    ApplicationInsightsHandler properties and event properties.
    """

    def __init__(
        self, name: str, handler_properties: Dict[str, Any], **kwargs: Dict[str, Any]
    ):
        self.name = name
        self.start_event_time = datetime.utcnow()
        self.end_event_time = datetime.utcnow() - timedelta(seconds=1)
        self.event_properties = handler_properties
        self.event_properties["PreciseTimeStamp"] = str(self.start_event_time)
        self.event_properties["ObjectType"] = kwargs.get("ObjectType", None) or ""
        self.event_properties["ObjectUri"] = kwargs.get("ObjectUri", None) or ""

    def _end_event(self):
        """
        End the event and update the ElapsedTime property.
        """
        self.end_event_time = datetime.utcnow()
        self.event_properties["ElapsedTime"] = str(
            self.end_event_time - self.start_event_time
        )

    def update_properties(self, update_dict: Dict[str, Any]):
        """
        Update the event properties with the given dict.
        """
        self.event_properties.update(update_dict)

    def upload_event(self, api_response: Dict[str, str], debug: bool):
        """
        The client can send an api_response to provide final details for the
        event, such as success or failure message. Parse the response with _parse_api_response,
        update the timing properties with a call to _end_event, and then upload
        the event to Application Insights.
        """
        self._parse_api_response(api_response)
        self._end_event()
        upload_start_time = datetime.utcnow()
        appInsightsLogger.warning(
            self.name, extra={"custom_dimensions": self.event_properties}
        )
        upload_end_time = datetime.utcnow()
        if debug:
            console_logger.info(
                "Application Insights upload of event {} took {}\n".format(
                    self.name, (upload_end_time - upload_start_time)
                )
            )

    def _parse_api_response(self, api_response: Dict[str, str]):
        succeeded = True if api_response.get("status", "") == "Succeeded" else False
        error_message = api_response.get("errorMessage", "")
        self.event_properties["ActionSuccess"] = succeeded
        self.event_properties["ActionFailureMessage"] = error_message


class ApplicationInsightsHandler(ApplicationInsightsHandlerInterface):
    """
    This class provides abstraction over the logging handler that sends
    custom events to Application Insights. Initialization of the handler sets
    some properties, such as workspace, that will not be changed during the
    lifetime of the ApplicationInsightsHandler. Using the handler then allows
    the client to create, update, and upload individual events.
    """

    def __init__(self, workspace: str, api_url: str, session_id: str, user_id: str):
        self.handler_properties = {
            "Workspace": workspace,
            "ServiceCloud": self._get_service_cloud(api_url),
            "SessionId": session_id,
            "UserId": user_id,
            "CLIVersion": __version__,
        }

    def create_event(self, event_name: str, **kwargs: Any) -> CustomEventInterface:
        """
        Create and return a CustomEvent object. All handlers properties are passed
        though and become properties on the event as well.
        """
        return CustomEvent(event_name, self.handler_properties, **kwargs)

    def _get_service_cloud(self, api_url: str) -> str:
        """
        Returns a string representing which ServiceCloud the event is hitting,
        derived from the api_url.
        """
        if api_url == "https://cp-api.bons.ai":
            return "Prod"
        elif api_url == "https://stagingkube-cp-api.azdev.bons.ai":
            return "Staging"
        elif api_url == "https://preprodkube-cp-api.aztest.bons.ai":
            return "Preprod"
        else:
            return "Unknown api_url {}".format(api_url)
