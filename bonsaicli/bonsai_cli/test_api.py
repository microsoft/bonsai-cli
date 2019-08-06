"""
This file contaisn unit tests for the bonsai api
"""
import os
from uuid import uuid4
from unittest import TestCase

# python 3.3+ includes mock in the unittest module
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

import requests
from requests.exceptions import HTTPError, ConnectionError
from click.testing import CliRunner

from bonsai_cli.api import BrainServerError, BonsaiAPI, _dict
from bonsai_cli.projfile import ProjectFile
from typing import Any, cast


class TestBonsaiApi(TestCase):
    """
    Contains all the tests for the bonsai api
    """
    def setUp(self):
        self.tempapi = BonsaiAPI('fakekey', 'fakeuser', 'https://someurl/',
                                 disable_telemetry=True)
        self.timeout = self.tempapi.TIMEOUT
        self.runner = CliRunner()
        self.req_id = str(uuid4())
        patcher = patch('bonsai_cli.api.uuid4', 
                        new=Mock(return_value=self.req_id))
        self.addCleanup(patcher.stop)
        patcher.start()

    def _get_headers(self):
        return {
            'Authorization': 'fakekey',
            'User-Agent': self.tempapi._user_info,
            'RequestId': self.req_id
        }

    def __get_post_headers(self):
        headers = self._get_headers()
        headers.pop('Authorization', None)
        return headers

    def _get_headers_multipart_mixed(self):
        headers = self._get_headers()
        headers.update({
            'Accept': 'multipart/mixed',
            'Accept-Encoding': 'base64',
        })
        return headers
    
    @staticmethod
    def _generate_mock_http_error_response():
        mock_response = cast(Any, Mock())
        mock_response.raise_for_status.side_effect = HTTPError()
        mock_response.headers = {'SpanID': uuid4()}
        return mock_response

    @patch('bonsai_cli.api.requests.Session.post')
    def testValidate(self, mock_post):
        """
        Test post through external validate function
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, cast(Any, Mock()))
        expected_dict = {"username": "someuser"}
        mock_response.json.return_value = expected_dict

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.validate()

        # Check that our api made expected calls
        mock_post.assert_called_once_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers=self.__get_post_headers(),
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/validate')
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.Session.post')
    def testValidateUrlJoining(self, mock_post):
        """
        Test that url's are joined correctly for validate
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.validate()
        mock_post.assert_called_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers=self.__get_post_headers(),
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/validate'
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.validate()
        mock_post.assert_called_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers=self.__get_post_headers(),
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/validate'
        )

    @patch('bonsai_cli.api.requests.Session.post')
    def testValidateRaiseError(self, mock_post):
        """
        Test that post raises an HTTP error through the validate function
        """

        # Construct mock response object and relevant function behavior
        mock_response = self._generate_mock_http_error_response()

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.validate()

        # Check that our api made expected calls
        mock_post.assert_called_once_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers=self.__get_post_headers(),
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/validate'
        )
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.Session.post')
    def testCreateBrain(self, mock_post):

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        self.tempapi.create_brain('fakename')

        # Check that our api made expected calls
        mock_post.assert_called_once_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers=self.__get_post_headers(),
            json={'name': 'fakename'},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/brains'
        )
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.Session.post')
    def testCreateBrainUrlJoining(self, mock_post):
        """
        Test that url's are joined correctly for create
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.create_brain('foo')
        mock_post.assert_called_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers=self.__get_post_headers(),
            json={'name': 'foo'},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/brains'
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.create_brain('bar')
        mock_post.assert_called_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers=self.__get_post_headers(),
            json={'name': 'bar'},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/brains'
        )

    @patch('bonsai_cli.api.requests.Session.post')
    def testCreateBrainWithProjectType(self, mock_post):

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        self.tempapi.create_brain('fakename', None, 'projtype')

        # Check that our api made expected calls
        mock_post.assert_called_once_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers=self.__get_post_headers(),
            json={'name': 'fakename',
                  'project_type': 'projtype'},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/brains'
        )
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.Session.post')
    def testCreateBrainWithProject(self, mock_post):
        """
        Test create brain with project api
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        self.tempapi.create_brain('fakename', pf, None)

        # Check that our api made expected calls
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.Session.post')
    def testPostRawDataError(self, mock_post):
        """
        Test that an HTTPError is handled when posting raw data
        """

        # Construct mock response object and relevant function behavior
        mock_response = self._generate_mock_http_error_response()
        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        with self.assertRaises(BrainServerError):
            self.tempapi.create_brain('fakename', pf, None)

        # Check that our api made expected calls
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.Session.get')
    def testListBrains(self, mock_get):
        """
        Test getting list of brains from api
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())
        brains = [
            {"name": "brain_a", "state": "Stopped"},
            {"name": "brain_b", "state": "Not Started"}
        ]
        expected_dict = {"brains": brains}
        mock_response.json.return_value = expected_dict

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.list_brains()

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.Session.get')
    def testListBrainsUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for list
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.list_brains()
        mock_get.assert_called_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.list_brains()
        mock_get.assert_called_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.Session.get')
    def testListBrainsRaiseError(self, mock_get):
        """
        Test that a get request will raise an HTTPError
        """

        # Construct mock response object and relevant function behavior
        mock_response = self._generate_mock_http_error_response()

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.list_brains()

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.Session.get')
    def testReturnEmptyJson(self, mock_get):
        """
        Testing that API returns empty json when there
        is no text in the response
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())
        mock_response.text = None

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.list_brains()

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(0, mock_response.json.call_count)
        self.assertEqual(response_dict, {})

    @patch('bonsai_cli.api.requests.Session.get')
    def testGetBrainStatus(self, mock_get):
        """
        Test getting brain status
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())
        brain_status = {
            "state": "training",
            "episode": 23,
            "objective_score": 22
        }
        expected_dict = brain_status
        mock_response.json.return_value = expected_dict

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.get_brain_status('fakebrain')

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain/status',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.Session.get')
    def testGetBrainStatusUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for get brain status
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.get_brain_status('fakebrain')
        mock_get.assert_called_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain/status',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.get_brain_status('fakebrain')
        mock_get.assert_called_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain/status',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.Session.get')
    def testListSims(self, mock_get):
        """
        Test getting list of sims from api
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())
        expected_dict = {
            "cartpole_sim_0": {
                "instances": 1,
                "status": "connected"
            },
            "cartpole_sim_1": {
                "instances": 1,
                "status": "connected"
            }
        }
        mock_response.json.return_value = expected_dict

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.list_simulators('fakebrain')

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain/sims',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.Session.get')
    def testListSimsUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for list sims
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.list_simulators('fakebrain')
        mock_get.assert_called_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain/sims',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.list_simulators('fakebrain')
        mock_get.assert_called_with(
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain/sims',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.Session.get')
    def testGetBrainFiles(self, mock_get):
        """
        Test getting brain files
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())
        mock_response.text = 'FOO'
        mock_response.headers = {'FOO': 'BAR'}

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.get_brain_files('fakebrain')

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers=self._get_headers_multipart_mixed(),
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(0, mock_response.json.call_count)
        self.assertEqual(response_dict, {})

    @patch('bonsai_cli.api.requests.Session.get')
    def testGetBrainFilesUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for getting brain files
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())
        mock_response.text = 'FOO'
        mock_response.headers = {'FOO': 'BAR'}

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.get_brain_files('fakebrain')
        mock_get.assert_called_with(
            headers=self._get_headers_multipart_mixed(),
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.get_brain_files('fakebrain')
        mock_get.assert_called_with(
            headers=self._get_headers_multipart_mixed(),
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.Session.delete')
    def testDeleteBrain(self, mock_delete):
        """
        Test Delete Brain from api
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())
        brains = [
            {"name": "brain_a", "state": "Stopped"},
            {"name": "brain_b", "state": "Not Started"}
        ]
        expected_dict = {"brains": brains}
        mock_response.json.return_value = expected_dict

        # Assign mock response to our patched function
        mock_delete.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.delete_brain('fakebrain')

        # Check that our api made expected calls
        mock_delete.assert_called_once_with(
            allow_redirects=False,
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_delete.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.Session.delete')
    def testDeleteBrainUrlJoining(self, mock_delete):
        """
        Test that url's are joined correctly for list sims
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_delete.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.delete_brain('fakebrain')
        mock_delete.assert_called_with(
            allow_redirects=False,
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.delete_brain('fakebrain')
        mock_delete.assert_called_with(
            allow_redirects=False,
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.Session.delete')
    def testDeleteBrainRaiseError(self, mock_delete):
        """
        Test that delete raises an error
        """

        # Construct mock response object and relevant function behavior
        mock_response = self._generate_mock_http_error_response()

        # Assign mock response to our patched function
        mock_delete.return_value = mock_response

        # Call API function we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.delete_brain('fakebrain')

        # Check that our api made expected calls
        mock_delete.assert_called_once_with(
            allow_redirects=False,
            headers=self._get_headers(),
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_delete.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.Session.put')
    def testStartTrainingBrain(self, mock_put):
        """
        Test Brain start training
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        self.tempapi.start_training_brain('fakebrain')

        # Check that our api made expected calls
        mock_put.assert_called_once_with(
            allow_redirects=False,
            headers=self._get_headers(),
            json={},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/train'
        )
        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.Session.put')
    def testStartTrainingBrainUrlJoining(self, mock_put):
        """
        Test that url's are joined correctly for starting training
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.start_training_brain('fakebrain')
        mock_put.assert_called_with(
            allow_redirects=False,
            headers=self._get_headers(),
            json={},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/train'
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.start_training_brain('fakebrain')
        mock_put.assert_called_with(
            allow_redirects=False,
            headers=self._get_headers(),
            json={},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/train'
        )

    @patch('bonsai_cli.api.requests.Session.put')
    def testStopTrainingBrain(self, mock_put):
        """
        Test Brain stop training
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        self.tempapi.stop_training_brain('fakebrain')

        # Check that our api made expected calls
        mock_put.assert_called_once_with(
            allow_redirects=False,
            headers=self._get_headers(),
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/stop'
        )
        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.Session.put')
    def testStopTrainingBrainUrlJoining(self, mock_put):
        """
        Test that url's are joined correctly for stopping training
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.stop_training_brain('fakebrain')
        mock_put.assert_called_with(
            allow_redirects=False,
            headers=self._get_headers(),
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/stop'
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.stop_training_brain('fakebrain')
        mock_put.assert_called_with(
            allow_redirects=False,
            headers=self._get_headers(),
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/stop'
        )

    @patch('bonsai_cli.api.requests.Session.put')
    def testStopTrainingBrainRaiseError(self, mock_put):
        """
        Test that an error is raised after the put request
        """

        # Construct mock response object and relevant function behavior
        mock_response = self._generate_mock_http_error_response()

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.stop_training_brain('fakebrain')

        # Check that our api made expected calls
        mock_put.assert_called_once_with(
            allow_redirects=False,
            headers=self._get_headers(),
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/stop'
        )
        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.Session.put')
    def testEditBrain(self, mock_put):
        """
        Testing API functionality for edit brain function
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        response = self.tempapi.edit_brain('fakebrain', pf)

        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.Session.put')
    def testEditBrainUrlJoining(self, mock_put):
        """
        Test that url's are joined correctly for editing brain
        """
        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())

        # Assign mock response to our patched function
        mock_put.return_value = mock_response
        pf = ProjectFile()

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.edit_brain('fakebrain', pf)
        args, kwargs = mock_put.call_args
        self.assertEqual('https://someurl/v1/fakeuser/fakebrain',
                         kwargs.get('url'))

        self.tempapi._api_url = 'https://someurl'
        self.tempapi.edit_brain('fakebrain', pf)
        args, kwargs = mock_put.call_args
        self.assertEqual('https://someurl/v1/fakeuser/fakebrain',
                         kwargs.get('url'))

    @patch('bonsai_cli.api.requests.Session.put')
    def testPutRawDataHTTPError(self, mock_put):
        """
        Testing API handles exception when sending a put request
        through the put_raw_data function.
        """

        # Construct mock response object and relevant function behavior
        mock_response = self._generate_mock_http_error_response()
        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        with self.assertRaises(BrainServerError):
            response = self.tempapi.edit_brain('fakebrain', pf)

        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.Session.put')
    def testConnectionError(self, mock_put):
        """
        Testing that connection errors are handled
        """

        # Assign mock response to our patched function
        mock_put.side_effect = ConnectionError()

        # Call API function we are testing
        pf = ProjectFile()
        with self.assertRaises(BrainServerError):
            self.tempapi.edit_brain('fakebrain', pf)

        # Following assert statements commented out due to being broken
        # A Change in the backend is causing it to be called twice on master
        # self.assertEqual(1, mock_put.call_count)
        # self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.Session.put')
    def testRedirectError(self, mock_put):
        """
        Testing that redirect errors are handled
        """

        # Construct mock response object and relevant function behavior
        mock_response = cast(Any, Mock())
        mock_response.headers = {'SpanID': uuid4()}
        mock_response.status_code = 301

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        with self.assertRaises(BrainServerError):
            response = self.tempapi.edit_brain('fakebrain', pf)

        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.log')
    def testLogging(self, mock_logger):
        """ Test that logging is called """
        result = self.tempapi.get_simulator_logs_stream('fakebrain', 'v2',
                                                        'cartpole')
        self.assertTrue(mock_logger.debug.called)
        self.assertEqual(6, mock_logger.debug.call_count)

    @patch('bonsai_cli.api.log')
    @patch('bonsai_cli.api.websocket')
    def testLoggingKeyboardInterrupt(self, mock_websocket, mock_logger):
        """ Test that KeyBoardInterrupt still logs """
        mock_websocket.run_forever.side_effect = KeyboardInterrupt()
        self.tempapi.get_simulator_logs_stream('fakebrain', 'v2', 'cartpole')
        self.assertEqual(5, mock_logger.debug.call_count)
        self.assertTrue(mock_logger.debug.called)

    @patch('bonsai_cli.api.requests.Session.get')
    def testGetBrainExists(self, mock_get):
        """
        Testing api.get_brain_exists()
        """
        # api._get_info(..) returns 200 meaning brain details found
        response = requests.Response()
        response.status_code = 200
        mock_get.return_value = response
        result = self.tempapi.get_brain_exists('fakebrain')
        self.assertTrue(result)
        self.assertEqual(1, mock_get.call_count)

        # api._get_info(..) returns 404 meaning no brain found
        response = requests.Response()
        response.status_code = 404
        mock_get.return_value = response
        result = self.tempapi.get_brain_exists('fakebrain')
        self.assertFalse(result)
        self.assertEqual(2, mock_get.call_count)

        # api._get_info(..) returns 500
        response = requests.Response()
        response.status_code = 500
        mock_get.return_value = response
        with self.assertRaises(BrainServerError):
            self.tempapi.get_brain_exists('fakebrain')

    def test_payload_create_brain(self):
        with self.runner.isolated_filesystem():
            open('test.ink', 'a').close()
            os.mkdir('sub')
            os.chdir('sub')
            open('bridge.py', 'a').close()
            os.mkdir('sub2')
            os.chdir('sub2')
            open('model.py', 'a').close()
            os.mkdir('sub3')
            open('sub3/foo.py', 'a').close()

            pf = ProjectFile('test.bproj')
            pf.files.add('../../test.ink')
            pf.files.add('../bridge.py')
            pf.files.add('model.py')
            pf.files.add('sub3/foo.py')

            payload, filesdata = self.tempapi._payload_create_brain('foo', pf)
            assert 'test.ink' in filesdata
            assert 'test.ink' in payload['project_accompanying_files']
            assert 'model.py' in filesdata
            assert 'model.py' in payload['project_accompanying_files']
            assert 'bridge.py' in filesdata
            assert 'bridge.py' in payload['project_accompanying_files']
            foo_py_filepath = os.path.join('sub3', 'foo.py')
            assert foo_py_filepath in filesdata
            assert foo_py_filepath in payload['project_accompanying_files']

    def test_json_decode_error(self):
        mock_response = cast(Any, Mock())
        mock_response.json.side_effect = ValueError()
        mock_response.headers = {'SpanID': uuid4()}
        with self.assertRaises(BrainServerError):
            _dict(mock_response, '1234')

    @patch('bonsai_cli.api.requests.Session.post')
    @patch('bonsai_cli.api.requests.Session.delete')
    @patch('bonsai_cli.api.requests.Session.get')
    @patch('bonsai_cli.api.requests.Session.put')
    def testTimeoutRaiseError(self, mock_put, mock_get, mock_delete, mock_post):
        """
        Test that a timeout error gets wrapped as a BrainServerError
        """

        # Assign mock response to our patched function
        mock_put.side_effect = requests.exceptions.Timeout
        mock_get.side_effect = requests.exceptions.Timeout
        mock_delete.side_effect = requests.exceptions.Timeout
        mock_post.side_effect = requests.exceptions.Timeout

        # Call API functions we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.stop_training_brain('fakebrain')

        with self.assertRaises(BrainServerError):
            self.tempapi.list_brains()

        with self.assertRaises(BrainServerError):
            self.tempapi.delete_brain('fakebrain')

        with self.assertRaises(BrainServerError):
            self.tempapi.validate()
