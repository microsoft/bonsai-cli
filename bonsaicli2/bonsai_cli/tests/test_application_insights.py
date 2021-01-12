from unittest import TestCase
from unittest.mock import create_autospec, patch, MagicMock
from logging import Logger
from bonsai_cli import application_insights, api, cookies
from configparser import NoOptionError


class TestApplicationInsights(TestCase):
    def setUp(self):
        self.mockLogger = create_autospec(Logger)
        application_insights.appInsightsLogger = self.mockLogger
        self.workspace_properties = {
            "workspace": "fake_workspace",
            "api_url": "fake_api_url",
            "session_id": "fake_session_id",
            "user_id": "fake_user_id",
        }
        self.app_insights_event_handler = (
            application_insights.ApplicationInsightsHandler(
                self.workspace_properties["workspace"],
                self.workspace_properties["api_url"],
                self.workspace_properties["session_id"],
                self.workspace_properties["user_id"],
            )
        )
        self.fake_api_response_with_success = {
            "status": "Succeeded",
            "errorMessage": "",
        }
        self.fake_api_response_with_failure = {
            "status": "Failed",
            "errorMessage": "Here is an error message",
        }

    def test_create_custom_event(self):
        test_event = self.app_insights_event_handler.create_event(
            "FakeEventName",
            kwargs={
                "ObjectType": "fake_value",
                "ObjectUri": "fake_value",
                "random_object": "fake_value",
            },
        )
        # assert CustomEvent has all the properties the Event Handler does
        self.assertGreaterEqual(
            self.app_insights_event_handler.handler_properties.items(),
            test_event.event_properties.items(),
        )
        # assert CustomEvent has the correct passed in kwargs
        self.assertTrue("ObjectType" in test_event.event_properties.keys())
        self.assertTrue("ObjectUri" in test_event.event_properties.keys())
        # assert CustomEvent does not have the random passed in kwarg in properties
        self.assertFalse("random_object" in test_event.event_properties.keys())

    def test_update_properties_custom_event(self):
        test_event = self.app_insights_event_handler.create_event(
            "FakeEventNameCustomEvent",
            kwargs={
                "ObjectType": "fake_value",
                "ObjectUri": "fake_value",
                "random_object": "fake_value",
            },
        )
        test_event.update_properties({"another_fake_key": "another_fake_value"})
        self.assertTrue("another_fake_key" in test_event.event_properties.keys())
        self.assertEqual(
            "another_fake_value",
            test_event.event_properties.get("another_fake_key"),
        )

    def test_upload_event_api_response_success(self):
        test_event = self.app_insights_event_handler.create_event(
            "FakeEventNameResponseSuccess",
            kwargs={
                "ObjectType": "fake_value",
                "ObjectUri": "fake_value",
                "random_object": "fake_value",
            },
        )
        test_event.upload_event(self.fake_api_response_with_success, debug=False)
        self.assertEqual(True, test_event.event_properties.get("ActionSuccess"))
        self.assertEqual("", test_event.event_properties.get("ActionFailureMessage"))

    def test_upload_event_api_response_failure(self):
        test_event = self.app_insights_event_handler.create_event(
            "FakeEventNameResponseFailure",
            kwargs={
                "ObjectType": "fake_value",
                "ObjectUri": "fake_value",
                "random_object": "fake_value",
            },
        )
        test_event.upload_event(self.fake_api_response_with_failure, debug=False)
        self.assertEqual(False, test_event.event_properties.get("ActionSuccess"))
        self.assertNotEqual("", test_event.event_properties.get("ActionFailureMessage"))

    def test_upload_event_end_event_actions(self):
        test_event = self.app_insights_event_handler.create_event(
            "FakeEventNameEndEvent",
            kwargs={
                "ObjectType": "fake_value",
                "ObjectUri": "fake_value",
                "random_object": "fake_value",
            },
        )
        first_time = test_event.end_event_time
        self.assertIsNone(test_event.event_properties.get("ElapsedTime", None))
        test_event.upload_event(self.fake_api_response_with_success, debug=False)
        second_time = test_event.end_event_time
        self.assertNotEqual(first_time, second_time)
        self.assertGreaterEqual(test_event.end_event_time, test_event.start_event_time)
        self.assertIsNotNone(test_event.event_properties.get("ElapsedTime", None))

    def test_upload_event_log_called(self):
        test_event = self.app_insights_event_handler.create_event(
            "FakeEventNameLogCalled",
            kwargs={
                "ObjectType": "fake_value",
                "ObjectUri": "fake_value",
                "random_object": "fake_value",
            },
        )
        self.assertEqual(0, self.mockLogger.warning.call_count)
        test_event.upload_event(self.fake_api_response_with_success, debug=False)
        self.assertEqual(1, self.mockLogger.warning.call_count)

    @patch("bonsai_cli.cookies.CookieConfiguration")
    def test_disabling_app_insights(self, MockCookieConfiguration: MagicMock):
        cookie_config = MockCookieConfiguration()
        cookie_config.get_application_insights_value.return_value = "false"
        bonsai_api = api.BonsaiAPI(
            "access_key",
            "workspace_id",
            "tenant_id",
            "api_url",
            "gateway_url",
            cookie_config,
        )
        self.assertIsInstance(
            bonsai_api.application_insights_handler,
            application_insights.SkeletonApplicationInsightsHandler,
        )

    @patch("configparser.RawConfigParser")
    def test_app_insights_disabled_by_default(self, MockConfigParser: MagicMock):
        parser = MockConfigParser()
        parser.get.side_effect = NoOptionError("option", "section")
        cookie_config = cookies.CookieConfiguration(parser)
        bonsai_api = api.BonsaiAPI(
            "access_key",
            "workspace_id",
            "tenant_id",
            "api_url",
            "gateway_url",
            cookie_config,
        )
        self.assertIsInstance(
            bonsai_api.application_insights_handler,
            application_insights.SkeletonApplicationInsightsHandler,
        )
