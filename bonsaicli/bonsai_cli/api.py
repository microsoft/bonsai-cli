import logging

import requests
import requests.exceptions


_VALIDATE_URL_TEMPLATE = "{api_url}/v1/validate"
_LIST_BRAINS_URL_TEMPLATE = "{api_url}/v1/{username}"
_CREATE_BRAIN_URL_TEMPLATE = "{api_url}/v1/{username}/brains"
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

    def create_brain(self, brain_name):
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
        data = {"name": brain_name}
        return self._post(url=url, data=data)

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
