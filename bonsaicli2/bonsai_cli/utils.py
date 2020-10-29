"""
This file contains the utilities for version 2 of the bonsai command line
"""

__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2019, Microsoft Corp."

import click
import multiprocessing
from multiprocessing.dummy import Pool
import requests
import sys
import timeit
from typing import Any, Optional

from .logger import Logger
from . import __version__
from .config import Config
from .api import BonsaiAPI
from click._compat import get_text_stderr
from configparser import NoSectionError
from json import decoder

log = Logger()


def api(use_aad: bool):
    """
    Convenience function for creating and returning an API object.
    :return: An API object.
    """
    bonsai_config = Config(argv=sys.argv, use_aad=use_aad)
    verify_required_configuration(bonsai_config)

    return BonsaiAPI(
        access_key=bonsai_config.accesskey,
        workspace_id=bonsai_config.workspace_id,
        tenant_id=bonsai_config.tenant_id,
        api_url=bonsai_config.url,
        gateway_url=bonsai_config.gateway_url,
    )


def click_echo(text: str, fg: Optional[str] = None, bg: Optional[str] = None):
    """
    Wraps click.echo to print in color if color is enabled in config
    Currently only supports color printing. Update this function if you
    wish to add blinking, underline, reverse, and etc...

    param fg: foreground color,
    param bg: background color
    """
    try:
        config = Config(argv=sys.argv, use_aad=False)
        color = config.use_color
    except ValueError:
        color = False

    if color:
        click.secho(text, fg=fg, bg=bg)
    else:
        click.echo(text)


def get_version_checker(ctx: click.Context, interactive: bool):
    """
    param ctx: Click context
    param interactive: True if the caller is interactive
    """
    if ctx.obj["VERSION_CHECK"] and interactive:
        return AsyncCliVersionChecker()
    else:
        return NullCliVersionChecker()


class CliVersionCheckerInterface(object):
    """
    Checks the latest CLI version.

    This interface is purposefully not a context manager - it's annoying and
    unnecessary to spam version upgrades when commands are failing to run.
    """

    def check_cli_version(
        self, wait: bool = False, print_up_to_date: bool = True
    ) -> None:
        raise NotImplementedError("check_cli_version not implemented")


class AsyncCliVersionChecker(CliVersionCheckerInterface):
    """
    Checks the latest CLI version, asynchronously.
    """

    # When asked to produce a version check at the end of a command, we are
    # willing to let the command wait up to this amount of time total before
    # abandoning the version check.
    #
    # This is a balance between timely version notifications, and adding more
    # latency to our own commands if PyPi is slow or unavailable.
    #
    # TODO: PyPi does not have have a latency SLA. Perform a long-running
    # measurement experiment and back this up with actual percentiles.
    _GIVE_UP_TIME_SECONDS = 0.5

    def __init__(self):
        """
        Construct the checker.

        Kicks off a background task to determine the latest CLI version.
        """
        # Counter-intuitively a dummy multiprocessing Pool is actually
        # a thread pool, not a process pool. This is the fastest way of
        # spawning a worker thread, that works in both Python 2 and 3.
        #
        # This will never be closed - the threads are daemonic.
        self._pool = Pool(1)
        self._result = self._pool.apply_async(self._query_version)

    def check_cli_version(self, wait: bool, print_up_to_date: bool = True) -> None:
        """
        Compares local cli version with the one on PyPi.

        If latest version is not yet known and wait is False, this function
        blocks for a brief period of time to allow it to complete. If wait is
        instead True, this function blocks indefinitely for a response.
        """
        pypi_version, err = self._get_version_result(wait)

        # If we lack a latest version, only continue to print what we do know
        # when waitiing was a requirement. When it wasn't, this appears as
        # unexpected error output spam for an otherwise-innocent command.
        if pypi_version is None and not wait:
            return

        user_cli_version = __version__

        if not pypi_version:
            click_echo(
                "You are using bonsai-cli version " + user_cli_version, fg="yellow"
            )
            click_echo(
                "Unable to connect to PyPi and determine if CLI is up to date.",
                fg="red",
            )
            if isinstance(err, requests.exceptions.SSLError):
                click_echo(
                    "The following SSL error occurred while attempting to obtain"
                    " the version information from PyPi. \n\n{}\n\n".format(err)
                    + "SSL errors are usually a result of an out of date version of"
                    " OpenSSL and/or certificates that may need to be updated."
                    " We recommend updating your python install to a more"
                    " recent version. If this is not possible, 'pip install"
                    " requests[security]' may fix the problem.",
                    fg="red",
                )
            elif err:
                click_echo(
                    "The following error occurred while attempting to obtain the"
                    " version information from PyPi.\n\n{}\n".format(err),
                    fg="red",
                )
        elif user_cli_version != pypi_version:
            click_echo(
                "You are using bonsai-cli version " + user_cli_version, fg="yellow"
            )
            click_echo(
                "Bonsai update available. The most recent version is "
                + pypi_version
                + ".",
                fg="yellow",
            )
            click_echo(
                "Upgrade via pip using 'pip install --upgrade bonsai-cli'", fg="yellow"
            )
        elif print_up_to_date:
            click_echo(
                "You are using bonsai-cli version "
                + user_cli_version
                + ", Everything is up to date.",
                fg="green",
            )

    def _query_version(self):
        log.debug("Checking latest CLI version...")
        start_time = timeit.default_timer()

        pypi_url = "https://pypi.org/pypi/bonsai-cli/json"
        pypi_version = get_pypi_version(pypi_url)

        end_time = timeit.default_timer()
        elapsed = end_time - start_time
        log.debug("Checked latest CLI version in {} seconds.".format(elapsed))

        return pypi_version

    def _get_version_result(self, wait: bool):
        if wait:
            timeout = None
        else:
            timeout = self._GIVE_UP_TIME_SECONDS

        pypi_version = None
        err = None
        try:
            pypi_version = self._result.get(timeout)
        except multiprocessing.TimeoutError:
            log.debug("CLI version check has not completed")
        except requests.exceptions.SSLError as e:
            err = e
        except requests.exceptions.RequestException as e:
            err = e
        except (decoder.JSONDecodeError, KeyError) as e:
            err = e

        return pypi_version, err


class NullCliVersionChecker(CliVersionCheckerInterface):
    """
    Performs no CLI version checking, does nothing.
    """

    def check_cli_version(
        self, wait: bool = False, print_up_to_date: bool = True
    ) -> None:
        pass


class CustomClickException(click.ClickException):
    """ Custom click exception that prints exceptions in color """

    def __init__(self, message: str, color: bool):
        click.ClickException.__init__(self, message)
        self.color = color

    def show(self, file: Optional[str] = None):
        """ Override ClickException function show() to print in color """
        if file is None:
            file = get_text_stderr()

        if self.color:
            click.secho("Error: %s" % self.format_message(), file=file, fg="red")
        else:
            click.echo("Error: %s" % self.format_message(), file=file)


def get_pypi_version(pypi_url: str):
    """
    This function attempts to get the package information
    from PyPi. It returns None if the request is bad, json
    is not decoded, or we have a KeyError in json dict

    param pypi_url: Url of pypi package
    """
    pkg_request = requests.get(pypi_url)
    pkg_json = pkg_request.json()
    pypi_version = pkg_json["info"]["version"]
    return pypi_version


def list_profiles(config: Config):
    """
    Lists available profiles from configuration

    param config: Bonsai_ai.Config
    """
    profile: Optional[str] = config.profile
    click.echo("\nBonsai configuration file(s) found at {}".format(config.file_paths))
    click.echo("\nAvailable Profiles:")
    if profile:
        if profile == "DEFAULT":
            click.echo("  DEFAULT" + " (active)")
        else:
            click.echo("  DEFAULT")

        # Grab Profiles from bonsai config and list each one
        sections = config.section_list()
        for section in sections:
            if section == profile:
                click.echo("  " + section + " (active)")
            else:
                click.echo("  " + section)
    else:
        click.echo("No profiles found please run 'bonsai configure'.")


def print_profile_information(config: Config):
    """ Print current active profile information """
    try:
        profile: Any = config.profile
        profile_info = config.section_items(profile)
    except NoSectionError:
        profile_info = config.defaults().items()

    click.echo("\nBonsai configuration file(s) found at {}".format(config.file_paths))
    click.echo("\nProfile Information")
    click.echo("--------------------")
    if profile_info:
        for key, val in profile_info:
            click.echo(key + ": " + str(val))
    else:
        click.echo("No profiles found please run 'bonsai configure'.")


def raise_brain_server_error_as_click_exception(
    debug: bool = False, output: Optional[str] = None, test: bool = False, *args: Any
):
    try:
        config = Config(argv=sys.argv, use_aad=False)
        color = config.use_color
    except ValueError:
        color = False

    if output == "json":

        message = {
            "status": args[0].exception["status"],
            "statusCode": args[0].exception["statusCode"],
            "statusMessage": args[0].exception["errorDump"],
        }

        if test:
            message["elapsed"] = str(args[0].exception["elapsed"])
            message["timeTaken"] = str(args[0].exception["timeTaken"])

    else:
        message = args[0].exception["errorDump"]

    raise CustomClickException(str(message), color=color)


def raise_as_click_exception(*args: Any):
    """This function raises a ClickException with a message that contains
    the specified message and the details of the specified exception.
    This is useful for all of our commands to raise errors to the
    user in a consistent way.

    This function expects to be handed an Exception (or
    one of its subclasses), or a message string followed by an Exception.
    """
    try:
        config = Config(argv=sys.argv, use_aad=False)
        color = config.use_color
    except ValueError:
        color = False

    if args and len(args) == 1:
        raise CustomClickException(
            "An error occurred\n" "{}".format(str(args[0])), color=color
        )
    elif args and len(args) > 1:
        raise CustomClickException("{}\n{}".format(args[0], args[1]), color=color)
    else:
        raise CustomClickException("An error occurred", color=color)


def raise_unique_constraint_violation_as_click_exception(
    debug: bool, output: str, type: str, name: str, test: bool = False, *args: Any
):
    """This function raises a ClickException with a message that the specified object type already exists"""
    try:
        config = Config(argv=sys.argv, use_aad=False)
        color = config.use_color
    except ValueError:
        color = False

    if debug:
        if output == "json":

            message = {
                "status": args[0].exception["status"],
                "statusCode": args[0].exception["statusCode"],
                "statusMessage": "{}\n{}\n{}".format(
                    args[0].exception["exception"],
                    args[0].exception["errorCode"],
                    args[0].exception["errorMessage"],
                ),
            }

            if test:
                message["elapsed"] = str(args[0].exception["elapsed"])
                message["timeTaken"] = str(args[0].exception["timeTaken"])

        else:
            message = "{}\n{}\n{}".format(
                args[0].exception["exception"],
                args[0].exception["errorCode"],
                args[0].exception["errorMessage"],
            )

    else:
        if output == "json":
            message = {
                "status": args[0].exception["status"],
                "statusCode": args[0].exception["statusCode"],
                "statusMessage": "{} '{}' already exists".format(type, name),
            }

            if test:
                message["elapsed"] = str(args[0].exception["elapsed"])
                message["timeTaken"] = str(args[0].exception["timeTaken"])

        else:
            message = "{} '{}' already exists".format(type, name)

    raise CustomClickException(str(message), color=color)


def raise_not_found_as_click_exception(
    debug: bool,
    output: str,
    operation: str,
    type: str,
    name: str,
    test: bool = False,
    *args: Any
):
    """This function raises a ClickException with a message that the specified object does not exist"""
    try:
        config = Config(argv=sys.argv, use_aad=False)
        color = config.use_color
    except ValueError:
        color = False

    if debug:
        if output == "json":

            message = {
                "status": args[0].exception["status"],
                "statusCode": args[0].exception["statusCode"],
                "statusMessage": "{}\n{}\n{}".format(
                    args[0].exception["exception"],
                    args[0].exception["errorCode"],
                    args[0].exception["errorMessage"],
                ),
            }

            if test:
                message["elapsed"] = str(args[0].exception["elapsed"])
                message["timeTaken"] = str(args[0].exception["timeTaken"])
        else:
            message = "{}\n{}\n{}".format(
                args[0].exception["exception"],
                args[0].exception["errorCode"],
                args[0].exception["errorMessage"],
            )

    else:
        if output == "json":
            message = {
                "status": args[0].exception["status"],
                "statusCode": args[0].exception["statusCode"],
                "statusMessage": "{} '{}' not found".format(type, name),
            }

            if test:
                message["elapsed"] = str(args[0].exception["elapsed"])
                message["timeTaken"] = str(args[0].exception["timeTaken"])
        else:
            message = "{} '{}' not found".format(type, name)

    raise CustomClickException(str(message), color=color)


def raise_client_side_click_exception(
    debug: bool,
    output: str,
    test: bool,
    status_code: int,
    status_message: str,
    response: Any,
):
    """This function raises a ClickException that is generated on client side"""
    try:
        config = Config(argv=sys.argv, use_aad=False)
        color = config.use_color
    except ValueError:
        color = False

    if debug:
        if output == "json":

            message = {
                "status": "Failed",
                "statusCode": status_code,
                "statusMessage": status_message,
            }

            if test:
                message["elapsed"] = response["elapsed"]
                message["timeTaken"] = response["timeTaken"]
        else:
            message = status_message

    else:
        if output == "json":
            message = {
                "status": "Failed",
                "statusCode": status_code,
                "statusMessage": status_message,
            }

            if test:
                message["elapsed"] = response["elapsed"]
                message["timeTaken"] = response["timeTaken"]
        else:
            message = status_message

    raise CustomClickException(str(message), color=color)


def verify_required_configuration(bonsai_config: Config):
    """This function verifies that the user's configuration contains
    the information required for interacting with the Bonsai BRAIN api.
    If required configuration is missing, an appropriate error is
    raised as a ClickException.
    """
    messages = []
    missing_config = False

    if not bonsai_config.use_aad and not bonsai_config.accesskey:
        messages.append("Your access key is not configured.")
        missing_config = True

    if not bonsai_config.aad_client and not bonsai_config.workspace_id:
        messages.append("Your workspace_id is not confgured.")
        missing_config = True

    if missing_config:
        messages.append("Run 'bonsai configure' to update required configuration.")
        raise click.ClickException("\n".join(messages))
