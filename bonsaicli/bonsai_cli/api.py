import functools
import json
import logging
import os
import sys

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import click
import email
import requests
import requests.exceptions
from requests.compat import unquote
from bonsai_cli import __version__
from bonsai_ai.logger import Logger

from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata
import websocket

_VALIDATE_URL_PATH = "/v1/validate"
_LIST_BRAINS_URL_PATH_TEMPLATE = "/v1/{username}"
_CREATE_BRAIN_URL_PATH_TEMPLATE = "/v1/{username}/brains"
_DELETE_BRAIN_URL_PATH_TEMPLATE = "/v1/{username}/{brain}"
_EDIT_BRAIN_URL_PATH_TEMPLATE = "/v1/{username}/{brain}"
_GET_INFO_URL_PATH_TEMPLATE = "/v1/{username}/{brain}"
_SIMS_INFO_URL_PATH_TEMPLATE = "/v1/{username}/{brain}/sims"
_SIMS_LOGS_URL_PATH_TEMPLATE = (
    "/v1/{username}/{brain}/{version}/sims/{sim}/logs")
_SIM_LOGS_STREAM_URL_TEMPLATE = (
    "{ws_url}/v1/{username}/{brain}/{version}/sims/{sim}/logs/ws")
_STATUS_URL_PATH_TEMPLATE = "/v1/{username}/{brain}/status"
_TRAIN_URL_PATH_TEMPLATE = "/v1/{username}/{brain}/train"
_STOP_URL_PATH_TEMPLATE = "/v1/{username}/{brain}/stop"
_RESUME_URL_PATH_TEMPLATE = "/v1/{username}/{brain}/{version}/resume"


log = Logger()


class BrainServerError(Exception):
    """
    This is thrown for any errors.
    """
    pass


def _handle_and_raise(response, e):
    """
    This takes an exception and wraps it in a BrainServerError.
    :param response: The response from the server.
    :param e: The error raised by the requests call.
    """
    try:
        message = 'Request failed with error message:\n{}'.format(
            response.json()["error"])
    except:
        message = 'Request failed.'
    raise BrainServerError('{}\n{}'.format(e, message))


def _handles_connection_error(func):
    """
    Decorator for handling ConnectionErrors raised by the requests
    library, raises a BrainServerError instead.

    :param func: the function being decorated
    """
    @functools.wraps(func)
    def _handler(self, url, *args, **kwargs):
        try:
            return func(self, url, *args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            message = "Unable to connect to domain: {}".format(url)
            raise BrainServerError(message)

    return _handler


def _dict(response):
    """
    Translates the response from the server into a dictionary. The implication
    is that the server should send back a JSON response for every REST API
    request, and if for some reason, that response is missing, it should be
    treated as an empty JSON message rather than an error. This method will
    change empty responses into empty dictionaries. Responses that are not
    formatted as JSON will raise an exception.
    :param response: The response from the server.
    :return: Dictionary form the JSON text in the response.
    """
    if response and response.text and response.text.strip():
        return response.json()
    return {}


class BonsaiAPI(object):
    """
    This object is required to use the Bonsai API CLI, as it sets up the
    necessary URLs and communications for communicating with the Bonsai BRAIN
    backend.

    Errors, both client-side and server-side, are expressed as
    RuntimeError errors. The exception will contain details of the
    error, such as the failing response code and/or error message.
    """

    # constant class variable for request timeout time in seconds
    TIMEOUT = 300

    def __init__(self, access_key, user_name, api_url, ws_url=None):
        """
        Initializes the API object.
        :param access_key: The access key for the user. This can be obtained
                           from the bons.ai website. This argument is required.
        :param user_name: The name of the user. This argument is required,
                          unless a BonsaiAPI is being created to validate an
                          access key. That is the only scenario in which
                          user_name may be None.
        :param api_url: The URL to for the BRAIN REST API.
        :param ws_url: The websocket URL for the BRAIN API.
        """
        log.debug(
            'Bootstrapping the Bonsai API for user: {}'.format(user_name))
        self._access_key = access_key
        self._user_name = user_name
        self._api_url = api_url
        self._ws_url = ws_url
        self._user_info = self._get_user_info()
        log.debug('API URL = {}'.format(self._api_url))
        log.debug('WS URL = {}'.format(self._ws_url))
        log.debug('User Info = {}'.format(self._user_info))

    @staticmethod
    def _get_user_info():
        """ Get Information about user that will be passed into
            The 'User-Agent' header with requests """
        platform = sys.platform
        python_version = "{}.{}.{}".format(
            sys.version_info.major,
            sys.version_info.minor,
            sys.version_info.micro)
        bonsai_cli_version = __version__
        user_info = "bonsai-cli/{} (python {}; {})".format(
            bonsai_cli_version, python_version, platform)
        return user_info

    @_handles_connection_error
    def _post(self, url, data=None):
        """
        Issues a POST request.
        :param url: The URL being posted to.
        :param data: Any additional data to bundle with the POST, as a
                     dictionary. Defaults to None.
        """
        log.debug('POST to {} with data {}...'.format(url, str(data)))
        response = requests.post(url=url,
                                 auth=(self._user_name, self._access_key),
                                 headers={'User-Agent': self._user_info},
                                 json=data,
                                 allow_redirects=False,
                                 timeout=self.TIMEOUT)
        try:
            response.raise_for_status()
            self._raise_on_redirect(response)
            log.debug('POST {} results:\n{}'.format(url, response.text))
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    @_handles_connection_error
    def _post_raw_data(self, url, data=None, headers=None):
        """
        Issues a POST request without encoding data argument.
        :param url: The URL being posted to.
        :param data: Any additional data to bundle with the POST, as raw data
                     to be used as the body.
        """
        log.debug('POST raw data to {} ...'.format(url))
        headers_out = {'Authorization': self._access_key,
                       'User-Agent': self._user_info}
        if headers:
            headers_out.update(headers)

        response = requests.post(url=url,
                                 headers=headers_out,
                                 data=data,
                                 allow_redirects=False,
                                 timeout=self.TIMEOUT)

        try:
            response.raise_for_status()
            self._raise_on_redirect(response)
            log.debug('POST {} results:\n{}'.format(url, response.text))
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    @_handles_connection_error
    def _put_raw_data(self, url, data=None, headers=None):
        """
        Issues a POST request without encoding data argument.
        :param url: The URL being posted to.
        :param data: Any additional data to bundle with the POST, as raw data
                     to be used as the body.
        """
        log.debug('PUT raw data to {} ...'.format(url))
        headers_out = {'Authorization': self._access_key,
                       'User-Agent': self._user_info}
        if headers:
            headers_out.update(headers)

        response = requests.put(url=url,
                                headers=headers_out,
                                data=data,
                                allow_redirects=False,
                                timeout=self.TIMEOUT)

        try:
            response.raise_for_status()
            self._raise_on_redirect(response)
            log.debug('PUT {} results:\n{}'.format(url, response.text))
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    @_handles_connection_error
    def _put(self, url, data=None):
        """
        Issues a PUT request.
        :param url: The URL being PUT to.
        :param data: Any additional data to bundle with the POST, as a
                     dictionary. Defaults to None.
        """
        log.debug('PUT to {} with data {}...'.format(url, str(data)))
        response = requests.put(url=url,
                                headers={'Authorization': self._access_key,
                                         'User-Agent': self._user_info},
                                json=data,
                                allow_redirects=False,
                                timeout=self.TIMEOUT)
        try:
            response.raise_for_status()
            self._raise_on_redirect(response)
            log.debug('PUT {} results:\n{}'.format(url, response.text))
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    @_handles_connection_error
    def _get(self, url):
        """
        Issues a GET request.
        :param url: The URL being GET from.
        """
        log.debug('GET from {}...'.format(url))
        response = requests.get(url=url,
                                headers={'Authorization': self._access_key,
                                         'User-Agent': self._user_info},
                                timeout=self.TIMEOUT)
        try:
            response.raise_for_status()
            log.debug('GET {} results:\n{}'.format(url, response.text))
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    @_handles_connection_error
    def _get_multipart(self, url):
        """
        Issues a GET request for a multipart/mixed response
        and returns a dictionary of filename/data from the response.
        :param url: The URL being GET from.
        """
        log.debug('GET from {}...'.format(url))
        headers = {
            'Authorization': self._access_key,
            "Accept": "multipart/mixed",
            'Accept-Encoding': 'base64',
            'User-Agent': self._user_info
        }
        response = requests.get(url=url,
                                headers=headers,
                                timeout=self.TIMEOUT)
        try:
            response.raise_for_status()
            log.debug('GET {} results:\n{}'.format(url, response.text))

            # combine response's headers/response so its parsable together
            header_list = ["{}: {}".format(key, response.headers[key])
                           for key in response.headers]
            header_string = "\r\n".join(header_list)
            message = "\r\n\r\n".join([header_string, response.text])

            # email is kind of a misnomer for the package,
            # it includes a lot of utilities and we're using
            # it here to parse the multipart response,
            # which the requests lib doesn't help with very much
            parsed_message = email.message_from_string(message)

            # create a filename/data dictionary
            response = {}
            for part in parsed_message.walk():
                # make sure this part is a file
                file_header = part.get_filename(failobj=None)
                if file_header:
                    filename = unquote(file_header)
                    response[filename] = part.get_payload(decode=True)

            return response
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    @_handles_connection_error
    def _delete(self, url):
        """
        Issues a DELETE request.
        :param url: The URL to DELETE.
        """
        log.debug('DELETE {}...'.format(url))
        response = requests.delete(url=url,
                                   headers={'Authorization': self._access_key,
                                            'User-Agent': self._user_info},
                                   allow_redirects=False,
                                   timeout=self.TIMEOUT)
        try:
            response.raise_for_status()
            self._raise_on_redirect(response)
            log.debug('DELETE {} results:\n{}'.format(url, response.text))
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    def _compose_multipart(self, json_dict, filesdata):
        """ Composes multipart/mixed request for create/edit brain.

        The multipart message is constructed as 1st part application/json and
        subsequent file part(s).

        :param json: dictionary that will be json-encoded
        :param filesdata: dict of <filename> -> <filedata>
        """
        # requests 1.13 does not have high-level support for multipart/mixed.
        # Using lower-level modules to construct multipart/mixed per
        # http://stackoverflow.com/questions/26299889/
        # how-to-post-multipart-list-of-json-xml-files-using-python-requests
        fields = []

        # 1st part: application/json
        rf = RequestField(name="project_data", data=json.dumps(json_dict))
        rf.make_multipart(content_type='application/json')
        fields.append(rf)

        # Subsequent parts: file text
        for filename, filedata in filesdata.items():
            rf = RequestField(name=filename, data=filedata, filename=filename,
                              headers={'Content-Length': len(filedata)})
            rf.make_multipart(content_disposition='attachment',
                              content_type="application/octet-stream")
            fields.append(rf)

        # Compose message
        body, content_type = encode_multipart_formdata(fields)
        # "multipart/form-data; boundary=.." -> "multipart/mixed; boundary=.."
        content_type = content_type.replace("multipart/form-data",
                                            "multipart/mixed",
                                            1)
        headers = {'Content-Type': content_type}

        return (headers, body)

    def _raise_on_redirect(self, response):
        """ Raises an HTTPError if the response is 301.

        Substitute a helpful error message for the often confusing errors
        produced by default redirect logic.

        :param response: requests.Response object to be processed
        """
        if (response.status_code == 301):
            raise requests.exceptions.HTTPError(
                "{} Moved Permanently: Likely misconfigured url: {}".format(
                    response.status_code, self._api_url)
            )

    def get_simulator_logs_stream(self, brain_name, version, sim):
        log.debug(
            'Getting simulator logs follow for BRAIN {}'.format(brain_name))
        log.debug('BRAIN version: {}'.format(version))
        log.debug('Simulator: {}'.format(sim))
        # NOTE: We do not use urljoin for this function as it is broken
        #       for websocket urls in python 3.5.x
        url = _SIM_LOGS_STREAM_URL_TEMPLATE.format(
            ws_url=self._ws_url,
            username=self._user_name,
            brain=brain_name,
            version=version,
            sim=sim
        )
        handler = LogStreamHandler(url, self._access_key)
        handler.run()

    def validate(self):
        """
        Validates an access key. This is the only scenario in which user_name
        in the constructor may be None. If the request fails, an exception is
        raised. If valid, a dictionary containing the username for the access
        key is returned.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name=None)
        >>> bonsai_api.validate()
        >>>
        >>> {
        >>>     "username": "bill"
        >>> }
        >>>
        :return: Dictionary containing the user-name associated with the access
                 key.
        """
        log.debug('Validating access key')
        url = urljoin(self._api_url, _VALIDATE_URL_PATH)
        return self._post(url=url)

    def list_brains(self):
        """
        Returns a dictionary containing the BRAINs for the user. If the request
        fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.list_brains()
        >>>
        >>> {
        >>>     "brains": [
        >>>         {
        >>>             "name": "cartpole",
        >>>             "state": "Training"
        >>>         },
        >>>         {
        >>>             "name": "lunar-lander",
        >>>             "state": "Completed"
        >>>         }
        >>>     ]
        >>> }
        >>>
        :return: Dictionary of BRAINs.
        """
        log.debug('Getting list of brains for {}...'.format(self._user_name))
        url_path = _LIST_BRAINS_URL_PATH_TEMPLATE.format(
            username=self._user_name
        )
        url = urljoin(self._api_url, url_path)
        return self._get(url=url)

    def _create_brain_multipart(self, url, brain, project_file):
        payload, filesdata = self._payload_create_brain(brain, project_file)

        headers, body = self._compose_multipart(payload, filesdata)
        return self._post_raw_data(url, data=body, headers=headers)

    def _edit_brain_multipart(self, url, project_file):
        payload, filesdata = self._payload_edit_brain(project_file)

        headers, body = self._compose_multipart(payload, filesdata)
        return self._put_raw_data(url, data=body, headers=headers)

    def _payload_create_brain(self, brain_name, project_file):
        # Get list of absolute/relative paths for project files.
        abs_paths = []
        rel_paths = []
        proj_dir = project_file.directory()
        for rel_path in project_file._list_paths():
            abs_path = os.path.join(proj_dir, rel_path)
            rel_paths.append(rel_path)
            abs_paths.append(abs_path)

        # Prepare application/json payload.
        project_file_name = os.path.basename(project_file.project_path)
        json_payload = {
            "name": brain_name,
            "description": "",
            "project_file": {
                "name": project_file_name,
                "content": project_file.content
            },
            "project_accompanying_files": rel_paths
        }

        # { <filename_header> -> <file_data> }
        filesdata = {}
        for i in range(len(rel_paths)):
            abs_path, rel_path = abs_paths[i], rel_paths[i]

            with open(abs_path, 'rb') as f:
                filesdata[rel_path] = f.read()

        return json_payload, filesdata

    def _payload_edit_brain(self, project_file):
        # Construct edit brain json payload by re-using create brain payload
        # since only difference is omission of name field.
        payload, filesdata = self._payload_create_brain(None, project_file)
        del payload["name"]
        return payload, filesdata

    def create_brain(self, brain_name, project_file=None, project_type=None):
        """
        Issues a command to the BRAIN backend to create a BRAIN for training
        and prediction purposes. If the request fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.create_brain('cartpole')
        :param brain_name: The name of the BRAIN
        """
        log.debug('Creating a BRAIN named {}'.format(brain_name))
        url_path = _CREATE_BRAIN_URL_PATH_TEMPLATE.format(
            username=self._user_name
        )
        url = urljoin(self._api_url, url_path)
        if project_type:
            data = {"name": brain_name, "project_type": project_type}
            return self._post(url=url, data=data)
        elif project_file:
            return self._create_brain_multipart(url, brain_name, project_file)
        else:
            data = {"name": brain_name}
            return self._post(url=url, data=data)

    def delete_brain(self, brain_name):
        """
        Issues a command to the BRAIN backend to delete a BRAIN. If the request
        failes, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.delete_brain('cartpole')
        """
        log.debug('Deleting a brain named {}'.format(brain_name))
        url_path = _DELETE_BRAIN_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name
        )
        url = urljoin(self._api_url, url_path)
        return self._delete(url=url)

    def edit_brain(self, brain_name, project_file):
        """
        Issues a command to the BRAIN backend to edit a BRAIN's associated
        file(s) and project file.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.edit_brain('cartpole', ProjectFile())
        :param brain_name: The name of the BRAIN
        :param project_file: ProjectFile object
        """
        log.debug('Editing a brain named {}'.format(brain_name))
        url_path = _EDIT_BRAIN_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name
        )
        url = urljoin(self._api_url, url_path)
        return self._edit_brain_multipart(url, project_file)

    def get_brain_files(self, brain_name):
        """
        Issues a command to the BRAIN backend to get all source files
        for the given BRAIN. If the request fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.get_brain_files('cartpole')
        :param brain_name: The name of the BRAIN
        :param user_name: Override of class' user for the request
        """
        url_path = _GET_INFO_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name
        )
        url = urljoin(self._api_url, url_path)
        return self._get_multipart(url=url)

    def _get_info(self, brain_name):
        url_path = _GET_INFO_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name
        )
        url = urljoin(self._api_url, url_path)

        log.debug('GET from {}...'.format(url))
        response = requests.get(url=url,
                                headers={'Authorization': self._access_key,
                                         'User-Agent': self._user_info},
                                timeout=self.TIMEOUT)
        return response

    def get_brain_exists(self, brain_name):
        """
        Issues a command to the BRAIN backend to get brain details for a
        given brain name.
          On success status code, returns True.
          On 404 status code returns False
          If the request fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.get_brain_exists('cartpole')
        :param brain_name: The name of the BRAIN
        """
        response = self._get_info(brain_name)
        log.debug('status code: {}'.format(response.status_code))
        if response.status_code == 404:
            return False
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

        return True

    def list_simulators(self, brain_name):
        """
        Lists the simulators registered with this BRAIN. If the request fails,
        an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.list_simulators('cartpole')
        >>>
        >>> {
        >>>     "cartpole_sim_0": {
        >>>         "instances": 1,
        >>>         "status": "connected"
        >>>     },
        >>>     "cartpole_sim_1": {
        >>>         "instances": 1,
        >>>         "status": "connected"
        >>>     }
        >>> }
        >>>
        :param brain_name: The name of the BRAIN to get the simulators for.
        :return: Dictionary of simulators and their statuses.
        """
        log.debug('Getting simulators for BRAIN: {}'.format(brain_name))
        url_path = _SIMS_INFO_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name
        )
        url = urljoin(self._api_url, url_path)
        return self._get(url=url)

    def get_simulator_logs(self, brain_name, version, sim):
        """
        Get the logs for simulators registered with this BRAIN version. If the
        request fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.get_simulator_logs('cartpole', 'latest', '1')
        >>>
        :param brain_name: The name of the BRAIN to get the simulator logs for
        :param version: version of the BRAIN to get simulator logs for
        :param sim: simulator identifier (currently defaults to 1)
        :return: List of log lines.
        """
        log.debug('Getting simulator logs for BRAIN {}'.format(brain_name))
        log.debug('BRAIN version: {}'.format(version))
        log.debug('Simualtor: {}'.format(sim))
        url_path = _SIMS_LOGS_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name,
            version=version,
            sim=sim
        )
        url = urljoin(self._api_url, url_path)
        return self._get(url=url)

    def start_training_brain(self, brain_name, sim_local=True):
        """
        Starts training a BRAIN. Only BRAINs that aren't actively training or
        in the process of starting training or shutting down can be requested
        to have training start. If the request fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.start_training_brain('cartpole')
        :param brain_name: The name of the BRAIN to start training.
        """
        log.debug('Starting training for BRAIN {}'.format(brain_name))
        data = {} if sim_local else {'manage_simulator': True}
        url_path = _TRAIN_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name
        )
        url = urljoin(self._api_url, url_path)
        return self._put(url=url, data=data)

    def get_brain_status(self, brain_name):
        """
        Gets the status of the BRAIN. If the request fails, an exception is
        raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.get_brain_status('cartpole')
        >>>
        >>> {
        >>>     "state": "training",
        >>>     "episode": 23,
        >>>     "objective_score": 22.0
        >>> }
        >>>
        :param brain_name: The name of the BRAIN to obtain the status for.
        :return: Dictionary containing the BRAIN status.
        """
        log.debug('Get the status of BRAIN: {}'.format(brain_name))
        url_path = _STATUS_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name
        )
        url = urljoin(self._api_url, url_path)
        return self._get(url=url)

    def stop_training_brain(self, brain_name):
        """
        Stops training a BRAIN. Only BRAINs that are actively being trained can
        be stopped. If the request fails, an error is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.stop_training_brain('cartpole')
        :param brain_name: The name of the BRAIN to stop training.
        """
        log.debug('Stopping training for BRAIN: {}'.format(brain_name))
        url_path = _STOP_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name
        )
        url = urljoin(self._api_url, url_path)
        return self._put(url=url)

    def resume_training_brain(self, brain_name, brain_version, sim_local=True):
        """
        Resume training a BRAIN.
        TODO:UPDATE DOCSTRING
        """
        log.debug('Resume training for BRAIN: {}'.format(brain_name))
        data = {} if sim_local else {'manage_simulator': True}
        url_path = _RESUME_URL_PATH_TEMPLATE.format(
            username=self._user_name,
            brain=brain_name,
            version=brain_version
        )
        url = urljoin(self._api_url, url_path)
        return self._put(url=url, data=data)


class LogStreamHandler(object):

    def __init__(self, ws_url, access_key):
        self._ws_url = ws_url
        self._access_key = access_key

    def run(self):
        ws = websocket.WebSocketApp(
            self._ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=LogStreamHandler.on_close,
            header=['Authorization: {}'.format(self._access_key)]
        )
        ws.on_open = self._on_open
        log.debug("Starting websocket connection for bonsai log --follow...")

        proxy = self._get_proxy()
        log.debug('proxy: {}'.format(proxy))

        try:
            ws.run_forever(**proxy)
        except KeyboardInterrupt as e:
            log.debug("Handling user Ctrl+C")

    def _get_proxy(self):
        if self._ws_url.startswith('wss'):
            server = os.getenv('https_proxy')
        else:
            server = os.getenv('http_proxy')

        if server is None:
            server = os.getenv('all_proxy')

        proxy = {}
        if server:
            host_port = server.rsplit(':', 1)
            proxy['http_proxy_host'] = host_port[0]
            if len(host_port) > 1:
                proxy['http_proxy_port'] = host_port[1]

        return proxy

    def _on_message(self, ws, message):
        click.echo(message, nl=False)

    def _on_error(self, ws, error):
        if type(error) == KeyboardInterrupt:
            log.debug("Handling Ctrl+c ...")
            return
        click.echo("Error received for '{}': '{}'".format(self._ws_url, error))

    @staticmethod
    def on_close(ws, code, reason):
        log.debug("on_close()")
        if code is None or code == 1000:
            return

        click.echo("(code={}) {}".format(code, reason))

    def _on_open(self, ws):
        log.debug("_on_open()")
