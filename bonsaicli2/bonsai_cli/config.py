"""
This file contains the config class for version 2 of the bonsai command line
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2019, Microsoft Corp."

# pyright:reportPrivateUsage=false

import sys
import os
from configparser import RawConfigParser, NoSectionError
from os.path import expanduser, join
from argparse import ArgumentParser

from typing import Any, List, Optional
from urllib.parse import urlparse

from .logger import Logger
from .aad import AADClient

import click

log = Logger()

# .bonsaiconfig config file keys
_DEFAULT = "DEFAULT"
_ACCESSKEY = "accesskey"
_WORKSPACEID = "workspace_id"
_TENANTID = "tenant_id"
_URL = "url"
_GATEWAYURL = "gateway_url"
_PROFILE = "profile"
_USE_COLOR = "use_color"

# Default bonsai api url
_DEFAULT_URL = "https://api.bons.ai"

# file names
_DOT_BONSAI = ".bonsaiconfig"

# CLI help strings
_ACCESS_KEY_HELP = (
    "The access key to use when connecting to the BRAIN server. If "
    "specified, it will be used instead of any access key"
    "information stored in a bonsai config file."
)
_AAD_HELP = "Use Azure Active Directory authentication if no accesskey is set."
_WORKSPACE_ID_HELP = "Azure workspace id."
_TENANT_ID_HELP = "Azure tenant id."
_URL_HELP = "Bonsai server URL. The URL should be of the form " '"https://api.bons.ai"'
_GATEWAY_URL_HELP = (
    "Bonsai server gateway URL. The URL should be of the form " '"https://api.bons.ai"'
)
_VERBOSE_HELP = "Enables logging. Alias for --log=all"
_PERFORMANCE_HELP = "Enables time delta logging. Alias for --log=perf.all"
_LOG_HELP = """
    Enable logging. Parameters are a list of log domains.
    Using --log=all will enable all domains.
    Using --log=none will disable logging.
    """
_RECORD_HELP = """
    Enable record simulation data to a file (current) or
    external service (not yet implemented).
    Parameter is the target file for recorded data. Data format will be
    inferred from the file extension. Currently supports ".json" and ".csv".
    """


class Config(object):
    """
    Manages Bonsai configuration environments.

    Configuration information is pulled from different locations. This class
    helps keep it organized. Configuration information comes from environment
    variables, the user `~./.bonsaiconfig` file, a local `./.bonsaiconfig` file,
    command line arguments, and finally, parameters
    overridden in code.

    An optional `profile` key can be used to switch between different
    profiles stored in the `~/.bonsaiconfig` configuration file. The users active
    profile is selected if none is specified.

    Attributes:
        accesskey:     Users access key from the web.
                        (Example: 00000000-1111-2222-3333-000000000001)
        workspace_id:      Users login name.
        url:           URL of the server to connect to.
                        (Example: "https://api.bons.ai")
    """

    def __init__(
        self, argv: List[str] = sys.argv, profile: Any = None, use_aad: bool = False
    ):
        """
        Construct Config object with program arguments.
        Pass in sys.argv for command-line arguments and an
        optional profile name to select a specific profile.

        Arguments:
            argv:    A list of argument strings.
            profile: The name of a profile to select. (optional)
            use_aad: Use AAD authentication
        """
        self.aad_client = None
        self.accesskey = None
        self.workspace_id = None
        self.tenant_id = None
        self.url = None
        self.gateway_url = None
        self.use_color = True
        self.use_aad = use_aad

        self.verbose = False
        self.record_file = None
        self.record_enabled = False
        self.file_paths = set()
        self._config_parser = RawConfigParser(allow_no_value=True)
        self._read_config()
        self.profile = profile

        self._parse_config(_DEFAULT)
        self._parse_config(profile)
        self._parse_args(argv)

        if use_aad:
            self.aad_client = AADClient(self.tenant_id)
            self.accesskey = self.aad_client.get_access_token()

    def __repr__(self):
        """ Prints out a JSON formatted string of the Config state. """
        return (
            "{{"
            '"profile": "{self.profile!r}", '
            '"accesskey": "{self.accesskey!r}", '
            '"workspace_id": "{self.workspace_id!r}", '
            '"tenant_id": "{self.tenant_id!r}", '
            '"url": "{self.url!r}", '
            '"gateway_url": "{self.gateway_url!r}", '
            '"use_color": "{self.use_color!r}", '
            '"use_aad": "{self.use_aad!r}", '
            "}}".format(self=self)
        )

    def _parse_config(self, profile: Optional[str]):
        """ parse both the '~/.bonsaiconfig' and './.bonsaiconfig' config files. """

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
        assign_key(_URL)
        assign_key(_GATEWAYURL)
        assign_key(_USE_COLOR)

        # if url is none set it to default bonsai api url
        if self.url is None:
            self.url = _DEFAULT_URL
        elif not urlparse(self.url).scheme:
            # if no url scheme is supplied, assume https
            self.url = "https://{}".format(self.url)

    def _parse_args(self, argv: List[str]):
        """ parser command line arguments """
        if sys.version_info >= (3, 0):
            parser = ArgumentParser(allow_abbrev=False)
        else:
            parser = ArgumentParser()

        parser.add_argument("--accesskey", "--access-key", help=_ACCESS_KEY_HELP)
        parser.add_argument("--workspace_id", help=_WORKSPACE_ID_HELP)
        parser.add_argument("--tenant_id", help=_TENANT_ID_HELP)
        parser.add_argument("--url", help=_URL_HELP)
        parser.add_argument("--gateway_url", help=_GATEWAY_URL_HELP)
        parser.add_argument("--aad", action="store_true", help=_AAD_HELP)
        parser.add_argument("--verbose", action="store_true", help=_VERBOSE_HELP)
        parser.add_argument(
            "--performance", action="store_true", help=_PERFORMANCE_HELP
        )
        parser.add_argument("--log", nargs="+", help=_LOG_HELP)
        parser.add_argument("--record", nargs=1, default=None, help=_RECORD_HELP)

        args, remainder = parser.parse_known_args(argv[1:])

        if args.aad:
            self.use_aad = args.aad

        if args.accesskey is not None:
            self.accesskey = args.accesskey

        if args.workspace_id is not None:
            self.workspace_id = args.workspace_id

        if args.tenant_id is not None:
            self.tenant_id = args.tenant_id

        if args.url is not None:
            self.url = args.url

        if args.gateway_url is not None:
            self.gateway_url = args.url

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

        if remainder is not None:
            pass

    def _config_files(self):
        return [join(expanduser("~"), _DOT_BONSAI), join(".", _DOT_BONSAI)]

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
            # Write empty .bonsaiconfig to disk if no file is found
            self._write_dot_bonsaiconfig()

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
            self._config_parser.set(_DEFAULT, _PROFILE, "DEFAULT")
        else:
            self._config_parser.set(_DEFAULT, _PROFILE, str(section))

    def _write_dot_bonsaiconfig(self):
        """ Writes to .bonsaiconfig in users home directory """
        config_path = join(expanduser("~"), _DOT_BONSAI)
        try:
            with open(config_path, "w") as f:
                self._config_parser.write(f)
                return True
        except (FileNotFoundError, PermissionError):
            click.echo("Error: Unable to write .bonsaiconfig to {}".format(config_path))
            return False

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
        writes to the .bonsaiconfig file in the users home directory.
        """
        if not kwargs:
            return False
        for key, value in kwargs.items():
            if key.lower() == _PROFILE.lower():
                self._set_profile(value)
            else:
                try:
                    self._config_parser.set(self.profile, key, str(value))
                except NoSectionError:
                    # Create and set default profile if it does not exist in .bonsaiconfig
                    self._set_profile(self.profile)
                    self._config_parser.set(self.profile, key, str(value))

        if not self._write_dot_bonsaiconfig():
            return False

        self._parse_config(self.profile)

        return True
