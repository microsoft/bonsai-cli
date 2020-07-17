"""
This file contains the config class for version 2 of the bonsai command line
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2019, Microsoft Corp."

# pyright:reportPrivateUsage=false

import sys
import os
from configparser import RawConfigParser, NoSectionError
from os.path import expanduser, join, splitext
from os import environ
from argparse import ArgumentParser
import json

from typing import Any, List, Optional
from urllib.parse import urlparse, urlunparse
from urllib.request import getproxies

from .logger import Logger
from .aad import AADClient
from .exceptions import AuthenticationError

log = Logger()

# keys into for getproxies() dict
_ALL_PROXY = 'all'
_HTTP_PROXY = 'http'
_HTTPS_PROXY = 'https'

# .bonsai config file keys
_DEFAULT = 'DEFAULT'
_ACCESSKEY = 'accesskey'
_WORKSPACEID = 'workspace_id'
_TENANTID = 'tenant_id'
_SUBSCRIPTION = 'subscription'
_RESOURCEGROUP = 'resource_group'
_URL = 'url'
_GATEWAYURL = 'gateway_url'
_PROXY = 'proxy'
_PROFILE = 'profile'
_USE_COLOR = 'use_color'

# Default bonsai api url
_DEFAULT_URL = 'https://api.bons.ai'

# env variables, used in hosted containers
_BONSAI_HEADLESS = 'BONSAI_HEADLESS'
_BONSAI_TRAIN_BRAIN = 'BONSAI_TRAIN_BRAIN'

# file names
_DOT_BONSAI = '.bonsaiconfig'
_DOT_BRAINS = '.brains'

# CLI help strings
_ACCESS_KEY_HELP = \
    'The access key to use when connecting to the BRAIN server. If ' \
    'specified, it will be used instead of any access key' \
    'information stored in a bonsai config file.'
_AAD_HELP = 'Use Azure Active Directory authentication if no accesskey is set.'
_WORKSPACE_ID_HELP = 'Azure workspace id.'
_TENANT_ID_HELP = 'Azure tenant id.'
_SUBSCRIPTION_HELP = 'Azure subscription.'
_RESOURCE_GROUP_HELP = 'Azure resource group.'
_URL_HELP = \
    'Bonsai server URL. The URL should be of the form ' \
    '"https://api.bons.ai"'
_GATEWAY_URL_HELP = \
    'Bonsai server gateway URL. The URL should be of the form ' \
    '"https://api.bons.ai"'
_PROXY_HELP = 'Proxy server address and port. Example: localhost:3128'
_BRAIN_HELP = \
    """
    The name of the BRAIN to connect to. Unless a version is specified
    the BRAIN will connect for training.
    """
_PREDICT_HELP = \
    """
    If set, the BRAIN will connect for prediction with the specified
    version. May be a positive integer number or 'latest' for the most
    recent version.
        For example: --predict=latest or --predict=3
    """
_VERBOSE_HELP = "Enables logging. Alias for --log=all"
_PERFORMANCE_HELP = \
    "Enables time delta logging. Alias for --log=perf.all"
_LOG_HELP = \
    """
    Enable logging. Parameters are a list of log domains.
    Using --log=all will enable all domains.
    Using --log=none will disable logging.
    """
_RECORD_HELP = \
    """
    Enable record simulation data to a file (current) or
    external service (not yet implemented).
    Parameter is the target file for recorded data. Data format will be
    inferred from the file extension. Currently supports ".json" and ".csv".
    """
_RETRY_TIMEOUT_HELP = \
    """
    The time in seconds that reflects how long the simulator will attempt to
    reconnect to the backend. 0 represents do not reconnect. -1 represents
    retry forever. The default is set to 300 seconds (5 minutes).
    """
_NETWORK_TIMEOUT_HELP = \
    """
    Time in seconds to wait before retrying network connections.
    Must be greater than zero.
    """
_SDK3_HELP = 'Use the SDK3 protocol to connect with the platform.'
# legacy help strings
_TRAIN_BRAIN_HELP = "The name of the BRAIN to connect to for training."
_PREDICT_BRAIN_HELP = \
    """
    The name of the BRAIN to connect to for predictions. If you
    use this flag, you must also specify the --predict-version flag.
    """
_PREDICT_VERSION_HELP = \
    """
    The version of the BRAIN to connect to for predictions. This flag
    must be specified when --predict-brain is used. This flag will
    be ignored if it is specified along with --train-brain or
    --brain-url.
    """
_RECORDING_FILE_HELP = 'Unsupported.'

class Config(object):
    """
    Manages Bonsai configuration environments.

    Configuration information is pulled from different locations. This class
    helps keep it organized. Configuration information comes from environment
    variables, the user `~./.bonsai` file, a local `./.bonsai` file, the
    `./.brains` file, command line arguments, and finally, parameters
    overridden in code.

    An optional `profile` key can be used to switch between different
    profiles stored in the `~/.bonsai` configuration file. The users active
    profile is selected if none is specified.

    Attributes:
        accesskey:     Users access key from the web.
                        (Example: 00000000-1111-2222-3333-000000000001)
        workspace_id:      Users login name.
        url:           URL of the server to connect to.
                        (Example: "https://api.bons.ai")
        brain:         Name of the BRAIN to use.
        predict:       True is predicting against a BRAIN, False for training.
        brain_version: Version number of the brain to use for prediction.
        proxy:         Server name and port number of proxy to connect through.
                        (Example: "localhost:9000")

    Example Usage:
        import sys, bonsai_ai
        config = bonsai_ai.Config(sys.argv)
        print(config)
        if config.predict:
            ...

    """
    def __init__(self,
                 argv: List[str] = sys.argv,
                 profile: Any = None,
                 use_aad: bool = False,
                 require_workspace: bool = True):
        """
        Construct Config object with program arguments.
        Pass in sys.argv for command-line arguments and an
        optional profile name to select a specific profile.

        Arguments:
            argv:    A list of argument strings.
            profile: The name of a profile to select. (optional)
            control_plane_auth: Instance will be used on control plane
            use_aad: Use AAD authentication
        """
        self.accesskey = None
        self.workspace_id = None
        self.tenant_id = None
        self.url = None
        self.gateway_url = None
        self.use_color = True
        self.use_aad = use_aad
        self.sdk3 = False

        self.brain = None

        self.predict = False
        self.brain_version = 0
        self._proxy = None
        self._retry_timeout_seconds = 300
        self._network_timeout_seconds = 60

        self.verbose = False
        self.record_file = None
        self.record_enabled = False
        self.file_paths = set()
        self._config_parser = RawConfigParser(allow_no_value=True)
        self._read_config()
        self.profile = profile

        self._parse_env()
        self._parse_config(_DEFAULT)
        self._parse_config(profile)
        self._parse_brains()
        self._parse_args(argv)

        # parse args works differently in 2.7
        if sys.version_info >= (3, 0):
            self._parse_legacy(argv)

        self.aad_client = AADClient(self.tenant_id)
        self.accesskey = self.aad_client.get_access_token()

    def __repr__(self):
        """ Prints out a JSON formatted string of the Config state. """
        return '{{'\
            '\"profile\": \"{self.profile!r}\", ' \
            '\"accesskey\": \"{self.accesskey!r}\", ' \
            '\"workspace_id\": \"{self.workspace_id!r}\", ' \
            '\"brain\": \"{self.brain!r}\", ' \
            '\"url\": \"{self.url!r}\", ' \
            '\"use_color\": \"{self.use_color!r}\", ' \
            '\"predict\": \"{self.predict!r}\", ' \
            '\"brain_version\": \"{self.brain_version!r}\", ' \
            '\"proxy\": \"{self.proxy!r}\", ' \
            '\"retry_timeout\": \"{self.retry_timeout!r}\", ' \
            '\"network_timeout\": \"{self.network_timeout!r}\" ' \
            '}}'.format(self=self)

    @property
    def proxy(self):
        # shell-local environment vars get top precedence, falling back to
        # OS-specific registry/configuration values
        if self._proxy is not None:
            return self._proxy
        proxy_dict = getproxies()
        proxy = proxy_dict.get(_ALL_PROXY, None)
        http_proxy = proxy_dict.get(_HTTP_PROXY, None)
        if http_proxy is not None:
            proxy = http_proxy

        if self.url is not None:
            uri = urlparse(self.url)
            if uri.scheme == 'https':
                https_proxy = proxy_dict.get(_HTTPS_PROXY, None)
                if https_proxy is not None:
                    proxy = https_proxy

        return proxy

    @proxy.setter
    def proxy(self, proxy: str):
        uri = urlparse(proxy)
        uri.port
        self._proxy = proxy

    @property
    def record_format(self):
        """ The log record format, as inferred from the extension of
        the log filename"""
        if self.record_file:
            _, fmt = splitext(self.record_file)
            return fmt
        else:
            return None

    @property
    def retry_timeout(self):
        return self._retry_timeout_seconds

    @retry_timeout.setter
    def retry_timeout(self, value: int):
        if value < -1:
            raise ValueError(
                'Retry timeout must be a positive integer, 0, or -1.')
        self._retry_timeout_seconds = value

    @property
    def network_timeout(self):
        return self._network_timeout_seconds

    @network_timeout.setter
    def network_timeout(self, value: int):
        if value < 1:
            raise ValueError(
                'Network timeout must be a positive integer.')
        self._network_timeout_seconds = value

    def refresh_access_token(self):
        if self.aad_client:
            self.accesskey = self.aad_client.get_access_token()
            if not self.accesskey:
                raise AuthenticationError('Could not refresh AAD bearer token.')

    def _parse_env(self):
        ''' parse out environment variables used in hosted containers '''
        self.brain = environ.get(_BONSAI_TRAIN_BRAIN, None)
        headless = environ.get(_BONSAI_HEADLESS, None)
        if headless == 'True':
            self.headless = True

    def _parse_config(self, profile: Optional[str]):
        ''' parse both the '~/.bonsai' and './.bonsai' config files. '''

        # read the values
        def assign_key(key: str):
            if self._config_parser.has_option(section, key):
                if key.lower() == _USE_COLOR.lower():
                    self.__dict__[key] = self._config_parser.getboolean(section, key)
                else:
                    self.__dict__[key] = self._config_parser.get(section, key)

        # get the profile
        section = _DEFAULT
        if profile is None:
            if self._config_parser.has_option(_DEFAULT, _PROFILE):
                section = self._config_parser.get(_DEFAULT, _PROFILE)
                self.profile = section
        else:
            section = profile

        assign_key(_ACCESSKEY)
        assign_key(_WORKSPACEID)
        assign_key(_TENANTID)
        assign_key(_SUBSCRIPTION)
        assign_key(_RESOURCEGROUP)
        assign_key(_URL)
        assign_key(_GATEWAYURL)
        assign_key(_PROXY)
        assign_key(_USE_COLOR)

        # if url is none set it to default bonsai api url
        if self.url is None:
            self.url = _DEFAULT_URL
        elif not urlparse(self.url).scheme:
            # if no url scheme is supplied, assume https
            self.url = 'https://{}'.format(self.url)

    def _parse_brains(self):
        ''' parse the './.brains' config file
            Example:
                {"brains": [{"default": true, "name": "test"}]}
        '''
        data = {}
        try:
            with open(_DOT_BRAINS) as file:
                data = json.load(file)

                # parse file now
                for brain in data['brains']:
                    if brain['default'] is True:
                        self.brain = brain['name']
                        return

        # except FileNotFoundError: python3
        except IOError:
            return

    def _parse_legacy(self, argv: List[str]):
        ''' print support for legacy CLI arguments '''
        if sys.version_info >= (3, 0):
            optional = ArgumentParser(
                description="",
                allow_abbrev=False,
                add_help=False)
        else:
            optional = ArgumentParser(
                description="",
                add_help=False)

        optional.add_argument(
            '--legacy',
            action='store_true',
            help='Legacy command line options')
        optional.add_argument('--train-brain', help=_TRAIN_BRAIN_HELP)
        optional.add_argument('--predict-brain', help=_PREDICT_BRAIN_HELP)
        optional.add_argument('--predict-version', help=_PREDICT_VERSION_HELP)
        optional.add_argument('--recording-file', help=_RECORDING_FILE_HELP)
        args, remainder = optional.parse_known_args(argv)

        if args.train_brain is not None:
            self.brain = args.train_brain
            self.predict = False

        if args.predict_version is not None:
            self.predict = True
            if args.predict_version == "latest":
                self.brain_version = 0
            else:
                self.brain_version = int(args.predict_version)

        if remainder is not None:
            pass

    def _parse_args(self, argv: List[str]):
        ''' parser command line arguments '''
        if sys.version_info >= (3, 0):
            parser = ArgumentParser(allow_abbrev=False)
        else:
            parser = ArgumentParser()

        parser.add_argument(
            '--accesskey', '--access-key', help=_ACCESS_KEY_HELP)
        parser.add_argument('--workspace_id', help=_WORKSPACE_ID_HELP)
        parser.add_argument('--tenant_id', help=_TENANT_ID_HELP)
        parser.add_argument('--subscription', help=_SUBSCRIPTION_HELP)
        parser.add_argument('--resource_group', help=_RESOURCE_GROUP_HELP)
        parser.add_argument('--url', help=_URL_HELP)
        parser.add_argument('--gateway_url', help=_GATEWAY_URL_HELP)
        parser.add_argument('--proxy', help=_PROXY_HELP)
        parser.add_argument('--brain', help=_BRAIN_HELP)
        parser.add_argument(
            '--predict',
            help=_PREDICT_HELP,
            nargs='?',
            const='latest',
            default=None)
        parser.add_argument('--aad', action='store_true',
                            help=_AAD_HELP)
        parser.add_argument('--verbose', action='store_true',
                            help=_VERBOSE_HELP)
        parser.add_argument('--performance', action='store_true',
                            help=_PERFORMANCE_HELP)
        parser.add_argument('--log', nargs='+', help=_LOG_HELP)
        parser.add_argument('--record', nargs=1, default=None,
                            help=_RECORD_HELP)
        parser.add_argument('--retry-timeout', type=int,
                            help=_RETRY_TIMEOUT_HELP)
        parser.add_argument('--network-timeout', type=int,
                            help=_NETWORK_TIMEOUT_HELP)
        parser.add_argument('--sdk3', action='store_true',
                            help=_SDK3_HELP)

        args, remainder = parser.parse_known_args(argv[1:])

        if args.aad:
            self.use_aad = args.aad

        if args.accesskey is not None:
            self.accesskey = args.accesskey

        if args.workspace_id is not None:
            self.workspace_id = args.workspace_id

        if args.tenant_id is not None:
            self.tenant_id = args.tenant_id

        if args.subscription is not None:
            self.subscription = args.subscription

        if args.resource_group is not None:
            self.resource_group = args.resource_group

        if args.url is not None:
            self.url = args.url

        if args.gateway_url is not None:
            self.gateway_url = args.url

        if args.proxy is not None:
            self.proxy = args.proxy

        if args.brain is not None:
            self.brain = args.brain

        if args.verbose:
            self.verbose = args.verbose
            log.set_enable_all(args.verbose)

        if args.performance:
            # logging::log().set_enabled(true);
            # logging::log().set_enable_all_perf(true);
            pass

        if args.log is not None:
            for domain in args.log:
                log.set_enabled(domain)

        if args.record:
            self.record_file = args.record[0]
            self.record_enabled = True

        if args.retry_timeout is not None:
            self.retry_timeout = args.retry_timeout

        if args.network_timeout is not None:
            self.network_timeout = args.network_timeout

        if args.sdk3:
            self.sdk3 = True
            if sys.version_info < (3, 6):
                raise RuntimeError('Use of the --sdk3 flag requires '
                                   'Python 3.6 or greater')

        brain_version = None
        if args.predict is not None:
            if args.predict == "latest":
                brain_version = 0
            else:
                brain_version = args.predict
            self.predict = True

        # update brain_version after all args have been processed
        if brain_version is not None:
            brain_version = int(brain_version)
            if brain_version < 0:
                raise ValueError(
                    'BRAIN version number must be'
                    'positive integer or "latest".')
            self.brain_version = brain_version

        if remainder is not None:
            pass

    def _config_files(self):
        return [join(expanduser('~'), _DOT_BONSAI), join('.', _DOT_BONSAI)]

    def _read_config(self):
        # verify that at least one of the config files exists
        # as RawConfigParser ignores missing files
        found = False
        config_files = self._config_files()
        for path in config_files:
            if os.access(path, os.R_OK):
                found = True
                break
        if not found:
            # Write empty .bonsai to disk if no file is found
            self._write_dot_bonsai()

        self._config_parser.read(config_files)
        for path in config_files:
            if os.path.exists(path):
                self.file_paths.add(path)

    def _set_profile(self, section: Any):
        # Create section if it does not exist
        if not self._config_parser.has_section(section) and section != _DEFAULT:
            self._config_parser.add_section(section)

        # Set profile in class and config
        self.profile = section
        if section == _DEFAULT:
            self._config_parser.set(_DEFAULT, _PROFILE, 'DEFAULT')
        else:
            self._config_parser.set(_DEFAULT, _PROFILE, str(section))

    def _write_dot_bonsai(self):
        """ Writes to .bonsai in users home directory """
        config_path = join(expanduser('~'), _DOT_BONSAI)
        try:
            with open(config_path, 'w') as f:
                self._config_parser.write(f)
        except (FileNotFoundError, PermissionError):
            log.info('WARNING: Unable to write .bonsai to {}'.format(
                config_path))

    def websocket_url(self):
        """ Converts api url to websocket url """
        api_url = self.url or ''
        parsed_api_url = urlparse(api_url)

        if parsed_api_url.scheme == 'http':
            parsed_ws_url = parsed_api_url._replace(scheme='ws')
        elif parsed_api_url.scheme == 'https':
            parsed_ws_url = parsed_api_url._replace(scheme='wss')
        else:
            return None
        ws_url = urlunparse(parsed_ws_url)
        return ws_url

    def has_section(self, section: str):
        """Checks the configuration to see if section exists."""
        if section == _DEFAULT:
            return True
        return self._config_parser.has_section(section)

    def section_list(self):
        """ Returns a list of sections in config """
        return self._config_parser.sections()

    def section_items(self, section: str):
        """ Returns a dictionary of items in a section """
        return self._config_parser.items(section)

    def defaults(self):
        """ Returns an ordered dict of items in the DEFAULT section """
        return self._config_parser.defaults()

    def update(self, **kwargs: Any):
        """
        Updates the configuration with the Key/value pairs in kwargs and
        writes to the .bonsai file in the users home directory.
        """
        if not kwargs:
            return
        for key, value in kwargs.items():
            if key.lower() == _PROFILE.lower():
                self._set_profile(value)
            else:
                try:
                    self._config_parser.set(self.profile, key, str(value))
                except NoSectionError:
                    # Create and set default profile if it does not exist in .bonsai
                    self._set_profile(self.profile)
                    self._config_parser.set(self.profile, key, str(value))
        self._write_dot_bonsai()
        self._parse_config(self.profile)
