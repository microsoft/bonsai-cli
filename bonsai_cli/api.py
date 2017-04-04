import logging

import email
import requests
import requests.exceptions
from requests.compat import unquote

import os
import json
from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata

_VALIDATE_URL_TEMPLATE = "{api_url}/v1/validate"
_LIST_BRAINS_URL_TEMPLATE = "{api_url}/v1/{username}"
_CREATE_BRAIN_URL_TEMPLATE = "{api_url}/v1/{username}/brains"
_GET_INFO_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}"
_LOAD_INK_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/ink"
_SIMS_INFO_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/sims"
_STATUS_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/status"
_TRAIN_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/train"
_STOP_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/stop"


log = logging.getLogger(__name__)


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

    def __init__(self, access_key, user_name, api_url):
        """
        Initializes the API object.
        :param access_key: The access key for the user. This can be obtained
                           from the bons.ai website. This argument is required.
        :param user_name: The name of the user. This argument is required,
                          unless a BonsaiAPI is being created to validate an
                          access key. That is the only scenario in which
                          user_name may be None.
        :param api_url: The URL to for the BRAIN REST API.
        """
        log.debug('Bootstrapping the Bonsai API for user: %s', user_name)
        self._access_key = access_key
        self._user_name = user_name
        self._api_url = api_url
        log.debug('API URL = %s', self._api_url)

    def _post(self, url, data=None):
        """
        Issues a POST request.
        :param url: The URL being posted to.
        :param data: Any additional data to bundle with the POST, as a
                     dictionary. Defaults to None.
        """
        log.debug('POST to %s with data %s...', url, str(data))
        response = requests.post(url=url,
                                 headers={'Authorization': self._access_key},
                                 json=data)
        try:
            response.raise_for_status()
            log.debug('POST %s results:\n%s', url, response.text)
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    def _post_raw_data(self, url, data=None, headers=None):
        """
        Issues a POST request without encoding data argument.
        :param url: The URL being posted to.
        :param data: Any additional data to bundle with the POST, as raw data
                     to be used as the body.
        """
        log.debug('POST raw data to %s ...', url)
        headers_out = {'Authorization': self._access_key}
        if headers:
            headers_out.update(headers)
        response = requests.post(url=url, headers=headers_out, data=data)

        try:
            response.raise_for_status()
            log.debug('POST %s results:\n%s', url, response.text)
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    def _put(self, url, data=None):
        """
        Issues a PUT request.
        :param url: The URL being PUT to.
        :param data: Any additional data to bundle with the POST, as a
                     dictionary. Defaults to None.
        """
        log.debug('PUT to %s with data %s...', url, str(data))
        response = requests.put(url=url,
                                headers={'Authorization': self._access_key},
                                json=data)
        try:
            response.raise_for_status()
            log.debug('PUT %s results:\n%s', url, response.text)
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    def _get(self, url):
        """
        Issues a GET request.
        :param url: The URL being GET from.
        """
        log.debug('GET from %s...', url)
        response = requests.get(url=url,
                                headers={'Authorization': self._access_key})
        try:
            response.raise_for_status()
            log.debug('GET %s results:\n%s', url, response.text)
            return _dict(response)
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    def _get_multipart(self, url):
        """
        Issues a GET request for a multipart/mixed response
        and returns a dictionary of filename/data from the response.
        :param url: The URL being GET from.
        """
        log.debug('GET from %s...', url)
        headers = {
            'Authorization': self._access_key,
            "Accept": "multipart/mixed"
        }
        response = requests.get(url=url,
                                headers=headers)
        try:
            response.raise_for_status()
            log.debug('GET %s results:\n%s', url, response.text)

            # combine response's headers/response so its parsable together
            header_list = ["{}: {}".format(key, response.headers[key])
                           for key in response.headers]
            header_string = "\r\n".join(header_list)
            message = "\r\n".join([header_string, response.text])

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
                    response[filename] = part.get_payload()

            return response
        except requests.exceptions.HTTPError as e:
            _handle_and_raise(response, e)

    def _post_multipart(self, url, json_dict, filesdata):
        """ Issues a POST multipart/mixed request with leading application/json
        part and subsequent file part(s).

        :param url: url string
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
                              content_type="text/plain")
            fields.append(rf)

        # Compose message
        post_body, content_type = encode_multipart_formdata(fields)
        # "multipart/form-data; boundary=.." -> "multipart/mixed; boundary=.."
        content_type = content_type.replace("multipart/form-data",
                                            "multipart/mixed",
                                            1)

        headers = {'Content-Type': content_type}
        return self._post_raw_data(url, data=post_body, headers=headers)

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
        url = _VALIDATE_URL_TEMPLATE.format(api_url=self._api_url)
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
        log.debug('Getting list of brains for %s...', self._user_name)
        url = _LIST_BRAINS_URL_TEMPLATE.format(
            api_url=self._api_url,
            username=self._user_name
        )
        return self._get(url=url)

    def _create_brain_from_bproj(self, url, brain_name, project_file):
        # Get list of absolute/relative paths for project files.
        abs_paths = []
        rel_paths = []
        proj_dir = project_file.directory()
        for abs_path in project_file._list_paths():
            abs_paths.append(abs_path)

            rel_path = os.path.relpath(abs_path, proj_dir)
            rel_paths.append(rel_path)

        # Prepare application/json payload.
        json_payload = {
            "name": brain_name,
            "description": "",
            "project_file": {
                "name": project_file.project_path,
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

        return self._post_multipart(url=url, json_dict=json_payload,
                                    filesdata=filesdata)

    def create_brain(self, brain_name, project_file=None, project_type=None):
        """
        Issues a command to the BRAIN backend to create a BRAIN for training
        and prediction purposes. If the request fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.create_brain('cartpole')
        :param brain_name: The name of the BRAIN
        """
        log.debug('Creating a brain named %s for %s',
                  brain_name, self._user_name)
        url = _CREATE_BRAIN_URL_TEMPLATE.format(
            api_url=self._api_url,
            username=self._user_name
        )
        if project_type:
            data = {"name": brain_name, "project_type": project_type}
            return self._post(url=url, data=data)
        elif project_file:
            return self._create_brain_from_bproj(url, brain_name, project_file)
        else:
            data = {"name": brain_name}
            return self._post(url=url, data=data)

    def get_brain_files(self, brain_name):
        """
        Issues a command to the BRAIN backend to get all source files
        for the given BRAIN. If the request fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.get_brain_files('cartpole')
        :param brain_name: The name of the BRAIN
        :param user_name: Override of class' user for the request
        """
        url = _GET_INFO_URL_TEMPLATE.format(
            api_url=self._api_url,
            username=self._user_name,
            brain=brain_name
        )
        return self._get_multipart(url=url)

    def load_inkling_into_brain(self, brain_name, inkling_code):
        """
        Issues a command to the BRAIN to load the provided Inkling code into
        the BRAIN. If the request fails, for example, due to a failure to
        compile the Inkling code, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> inkling_code = '(Inkling code goes here)'
        >>> bonsai_api.load_inkling_into_brain(brain_name='foo',
        >>>                                    inkling_code=inkling_code)
        :param brain_name: The name of the BRAIN to load Inkling into.
        :param inkling_code: The Inkling code to load into the BRAIN.
        """
        log.debug('Loading BRAIN %s with Inkling:\n%s',
                  brain_name, inkling_code)
        url = _LOAD_INK_URL_TEMPLATE.format(
            api_url=self._api_url,
            username=self._user_name,
            brain=brain_name
        )
        data = {"ink_content": inkling_code}
        return self._post(url=url, data=data)

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
        log.debug('Getting simulators for BRAIN %s for %s',
                  brain_name, self._user_name)
        url = _SIMS_INFO_URL_TEMPLATE.format(
            api_url=self._api_url,
            username=self._user_name,
            brain=brain_name
        )
        return self._get(url=url)

    def start_training_brain(self, brain_name):
        """
        Starts training a BRAIN. Only BRAINs that aren't actively training or
        in the process of starting training or shutting down can be requested
        to have training start. If the request fails, an exception is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.start_training_brain('cartpole')
        :param brain_name: The name of the BRAIN to start training.
        """
        log.debug('Starting training for BRAIN %s for %s',
                  brain_name, self._user_name)
        url = _TRAIN_URL_TEMPLATE.format(
            api_url=self._api_url,
            username=self._user_name,
            brain=brain_name
        )
        return self._put(url=url)

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
        log.debug('Get the status of BRAIN %s for %s.',
                  brain_name, self._user_name)
        url = _STATUS_URL_TEMPLATE.format(
            api_url=self._api_url,
            username=self._user_name,
            brain=brain_name
        )
        return self._get(url=url)

    def stop_training_brain(self, brain_name):
        """
        Stops training a BRAIN. Only BRAINs that are actively being trained can
        be stopped. If the request fails, an error is raised.
        >>> bonsai_api = BonsaiAPI(access_key='foo', user_name='bill')
        >>> bonsai_api.stop_training_brain('cartpole')
        :param brain_name: The name of the BRAIN to stop training.
        """
        log.debug('Stopping training for BRAIN %s for %s',
                  brain_name, self._user_name)
        url = _STOP_URL_TEMPLATE.format(
            api_url=self._api_url,
            username=self._user_name,
            brain=brain_name
        )
        return self._put(url=url)
