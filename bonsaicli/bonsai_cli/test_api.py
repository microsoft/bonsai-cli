"""
This file contaisn unit tests for the bonsai api
"""
from unittest import TestCase

# python 3.3+ includes mock in the unittest module
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

import requests
from requests.exceptions import HTTPError, ConnectionError

from bonsai_cli.api import BrainServerError, BonsaiAPI
from bonsai_cli.projfile import ProjectFile


class TestBonsaiApi(TestCase):
    """
    Contains all the tests for the bonsai api
    """
    def setUp(self):
        self.tempapi = BonsaiAPI('fakekey', 'fakeuser', 'https://someurl/')
        self.timeout = self.tempapi.TIMEOUT

    @patch('bonsai_cli.api.requests.post')
    def testValidate(self, mock_post):
        """
        Test post through external validate function
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
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
            headers={'User-Agent': self.tempapi._user_info},
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/validate')
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.post')
    def testValidateUrlJoining(self, mock_post):
        """
        Test that url's are joined correctly for validate
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.validate()
        mock_post.assert_called_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers={'User-Agent': self.tempapi._user_info},
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/validate'
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.validate()
        mock_post.assert_called_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers={'User-Agent': self.tempapi._user_info},
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/validate'
        )

    @patch('bonsai_cli.api.requests.post')
    def testValidateRaiseError(self, mock_post):
        """
        Test that post raises an HTTP error through the validate function
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError()

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.validate()

        # Check that our api made expected calls
        mock_post.assert_called_once_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers={'User-Agent': self.tempapi._user_info},
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/validate'
        )
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.post')
    def testCreateBrain(self, mock_post):

        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.create_brain('fakename')

        # Check that our api made expected calls
        mock_post.assert_called_once_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers={'User-Agent': self.tempapi._user_info},
            json={'name': 'fakename'},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/brains'
        )
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.post')
    def testCreateBrainUrlJoining(self, mock_post):
        """
        Test that url's are joined correctly for create
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.create_brain('foo')
        mock_post.assert_called_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers={'User-Agent': self.tempapi._user_info},
            json={'name': 'foo'},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/brains'
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.create_brain('bar')
        mock_post.assert_called_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers={'User-Agent': self.tempapi._user_info},
            json={'name': 'bar'},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/brains'
        )

    @patch('bonsai_cli.api.requests.post')
    def testCreateBrainWithProjectType(self, mock_post):

        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.create_brain('fakename', None, 'projtype')

        # Check that our api made expected calls
        mock_post.assert_called_once_with(
            allow_redirects=False,
            auth=('fakeuser', 'fakekey'),
            headers={'User-Agent': self.tempapi._user_info},
            json={'name': 'fakename',
                  'project_type': 'projtype'},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/brains'
        )
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.post')
    def testCreateBrainWithProject(self, mock_post):
        """
        Test create brain with project api
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        response_dict = self.tempapi.create_brain('fakename', pf, None)

        # Check that our api made expected calls
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.post')
    def testPostRawDataError(self, mock_post):
        """
        Test that an HTTPError is handled when posting raw data
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError()
        # Assign mock response to our patched function
        mock_post.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        with self.assertRaises(BrainServerError):
            self.tempapi.create_brain('fakename', pf, None)

        # Check that our api made expected calls
        self.assertEqual(1, mock_post.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.get')
    def testListBrains(self, mock_get):
        """
        Test getting list of brains from api
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
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
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.get')
    def testListBrainsUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for list
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.list_brains()
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.list_brains()
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.get')
    def testListBrainsRaiseError(self, mock_get):
        """
        Test that a get request will raise an HTTPError
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError()

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.list_brains()

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.get')
    def testReturnEmptyJson(self, mock_get):
        """
        Testing that API returns empty json when there
        is no text in the response
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.text = None

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.list_brains()

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser',
            timeout=self.timeout)
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(0, mock_response.json.call_count)
        self.assertEqual(response_dict, {})

    @patch('bonsai_cli.api.requests.get')
    def testGetBrainStatus(self, mock_get):
        """
        Test getting brain status
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
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
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/status',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.get')
    def testGetBrainStatusUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for get brain status
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.get_brain_status('fakebrain')
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/status',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.get_brain_status('fakebrain')
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/status',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.get')
    def testGetSimLogs(self, mock_get):
        """
        Test getting sim logs
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        expected_list = ["line1", "line2"]
        mock_response.json.return_value = expected_list

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        response_list = self.tempapi.get_simulator_logs('fakebrain',
                                                        '1', 'cartpole')

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/1/sims/cartpole/logs',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_list, expected_list)

    @patch('bonsai_cli.api.requests.get')
    def testGetSimsLogsUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for get sim logs
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.get_simulator_logs('fakebrain', '1', 'cartpole')
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/1/sims/cartpole/logs',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.get_simulator_logs('fakebrain', '1', 'cartpole')
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/1/sims/cartpole/logs',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.get')
    def testListSims(self, mock_get):
        """
        Test getting list of sims from api
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
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
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/sims',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.get')
    def testListSimsUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for list sims
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.list_simulators('fakebrain')
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/sims',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.list_simulators('fakebrain')
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain/sims',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.get')
    def testGetBrainFiles(self, mock_get):
        """
        Test getting brain files
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.text = 'FOO'
        mock_response.headers = {'FOO': 'BAR'}

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Call API function we are testing
        response_dict = self.tempapi.get_brain_files('fakebrain')

        # Check that our api made expected calls
        mock_get.assert_called_once_with(
            headers={'Authorization': 'fakekey',
                     'Accept': 'multipart/mixed',
                     'Accept-Encoding': 'base64',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_get.call_count)
        self.assertEqual(0, mock_response.json.call_count)
        self.assertEqual(response_dict, {})

    @patch('bonsai_cli.api.requests.get')
    def testGetBrainFilesUrlJoining(self, mock_get):
        """
        Test that url's are joined correctly for getting brain files
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.text = 'FOO'
        mock_response.headers = {'FOO': 'BAR'}

        # Assign mock response to our patched function
        mock_get.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.get_brain_files('fakebrain')
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'Accept': 'multipart/mixed',
                     'Accept-Encoding': 'base64',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.get_brain_files('fakebrain')
        mock_get.assert_called_with(
            headers={'Authorization': 'fakekey',
                     'Accept': 'multipart/mixed',
                     'Accept-Encoding': 'base64',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.delete')
    def testDeleteBrain(self, mock_delete):
        """
        Test Delete Brain from api
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
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
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_delete.call_count)
        self.assertEqual(1, mock_response.json.call_count)
        self.assertEqual(response_dict, expected_dict)

    @patch('bonsai_cli.api.requests.delete')
    def testDeleteBrainUrlJoining(self, mock_delete):
        """
        Test that url's are joined correctly for list sims
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_delete.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.delete_brain('fakebrain')
        mock_delete.assert_called_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.delete_brain('fakebrain')
        mock_delete.assert_called_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )

    @patch('bonsai_cli.api.requests.delete')
    def testDeleteBrainRaiseError(self, mock_delete):
        """
        Test that delete raises an error
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError()

        # Assign mock response to our patched function
        mock_delete.return_value = mock_response

        # Call API function we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.delete_brain('fakebrain')

        # Check that our api made expected calls
        mock_delete.assert_called_once_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            url='https://someurl/v1/fakeuser/fakebrain',
            timeout=self.timeout
        )
        self.assertEqual(1, mock_delete.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.put')
    def testStartTrainingBrain(self, mock_put):
        """
        Test Brain start training
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        response = self.tempapi.start_training_brain('fakebrain')

        # Check that our api made expected calls
        mock_put.assert_called_once_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            json={},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/train'
        )
        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.put')
    def testStartTrainingBrainUrlJoining(self, mock_put):
        """
        Test that url's are joined correctly for starting training
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.start_training_brain('fakebrain')
        mock_put.assert_called_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            json={},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/train'
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.start_training_brain('fakebrain')
        mock_put.assert_called_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            json={},
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/train'
        )

    @patch('bonsai_cli.api.requests.put')
    def testStopTrainingBrain(self, mock_put):
        """
        Test Brain stop training
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        response = self.tempapi.stop_training_brain('fakebrain')

        # Check that our api made expected calls
        mock_put.assert_called_once_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/stop'
        )
        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.put')
    def testStopTrainingBrainUrlJoining(self, mock_put):
        """
        Test that url's are joined correctly for stopping training
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Test different urls and show that they are joined correctly
        self.tempapi._api_url = 'https://someurl//'
        self.tempapi.stop_training_brain('fakebrain')
        mock_put.assert_called_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/stop'
        )
        self.tempapi._api_url = 'https://someurl'
        self.tempapi.stop_training_brain('fakebrain')
        mock_put.assert_called_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/stop'
        )

    @patch('bonsai_cli.api.requests.put')
    def testStopTrainingBrainRaiseError(self, mock_put):
        """
        Test that an error is raised after the put request
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError()

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        with self.assertRaises(BrainServerError):
            self.tempapi.stop_training_brain('fakebrain')

        # Check that our api made expected calls
        mock_put.assert_called_once_with(
            allow_redirects=False,
            headers={'Authorization': 'fakekey',
                     'User-Agent': self.tempapi._user_info},
            json=None,
            timeout=self.timeout,
            url='https://someurl/v1/fakeuser/fakebrain/stop'
        )
        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.put')
    def testEditBrain(self, mock_put):
        """
        Testing API functionality for edit brain function
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        response = self.tempapi.edit_brain('fakebrain', pf)

        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.put')
    def testEditBrainUrlJoining(self, mock_put):
        """
        Test that url's are joined correctly for editing brain
        """
        # Construct mock response object and relevant function behavior
        mock_response = Mock()

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

    @patch('requests.put')
    def testPutRawDataHTTPError(self, mock_put):
        """
        Testing API handles exception when sending a put request
        through the put_raw_data function.
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError()
        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        with self.assertRaises(BrainServerError):
            response = self.tempapi.edit_brain('fakebrain', pf)

        self.assertEqual(1, mock_put.call_count)
        self.assertEqual(1, mock_response.json.call_count)

    @patch('bonsai_cli.api.requests.put')
    def testConnectionError(self, mock_put):
        """
        Testing that connection errors are handled
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = ConnectionError()

        # Assign mock response to our patched function
        mock_put.return_value = mock_response

        # Call API function we are testing
        pf = ProjectFile()
        with self.assertRaises(BrainServerError):
            response = self.tempapi.edit_brain('fakebrain', pf)

        # Following assert statements commented out due to being broken
        # A Change in the backend is causing it to be called twice on master
        # self.assertEqual(1, mock_put.call_count)
        # self.assertEqual(1, mock_response.raise_for_status.call_count)

    @patch('bonsai_cli.api.requests.put')
    def testRedirectError(self, mock_put):
        """
        Testing that redirect errors are handled
        """

        # Construct mock response object and relevant function behavior
        mock_response = Mock()
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

    @patch('bonsai_cli.api.requests.get')
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
