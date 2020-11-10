"""
This file contains the main code for version 2 of the bonsai command line,
the command line can be used to interact with the bonsai service.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2020, Microsoft Corp."

import os
import platform
import pkg_resources
import pprint
import sys
import click

from typing import Any, Dict, Optional

from bonsai_cli.aad import get_aad_cache_file
from bonsai_cli.api import BonsaiAPI
from bonsai_cli.config import Config
from bonsai_cli.logger import Logger
from bonsai_cli.utils import (
    get_version_checker,
    AsyncCliVersionChecker,
    print_profile_information,
    list_profiles,
    raise_as_click_exception,
)

from .brain import brain
from .exportedbrain import exportedbrain
from .simulator import simulator

log = Logger()

""" Global variable for click context settings following the conventions
from the click documentation. It can be modified to add more context
settings if they are needed in future development of the cli.
"""
CONTEXT_SETTINGS: Dict[str, Any] = dict(help_option_names=["--help", "-h"])


def _version_callback(ctx: click.Context, value: str):
    """
    This is the callback function when --version option
    is used. The function lets the user know what version
    of the cli they are currently on and if there is an
    update available.
    """
    if not value or ctx.resilient_parsing:
        return
    AsyncCliVersionChecker().check_cli_version(wait=True)
    ctx.exit()


def _sysinfo(ctx: click.Context, value: str):
    if not value or ctx.resilient_parsing:
        return
    click.echo("\nPlatform Information\n--------------------")
    click.echo(sys.version)
    click.echo(platform.platform())
    packages = [d for d in iter(pkg_resources.working_set)]
    click.echo("\nPackage Information\n-------------------")
    click.echo(pprint.pformat(packages))
    click.echo("\nBonsai Profile Information\n--------------------------")
    print_profile_information(Config(use_aad=True))
    ctx.exit()


def _set_color(ctx: click.Context, value: str):
    """ Set use_color flag in bonsai config """
    if value is None or ctx.resilient_parsing:
        return

    # no need for AAD authentication if only setting color
    config = Config(use_aad=False)
    if value:
        config.update(use_color=True)
    else:
        config.update(use_color=False)
    ctx.exit()


@click.command(
    "configure",
    short_help="Configure your Bonsai resources and authenticate with the Bonsai server.",
)
@click.option("--workspace-id", "-w", help="[Required] Workspace ID.")
@click.option("--tenant-id", help="Tenant ID.")
@click.option(
    "--show",
    is_flag=True,
    help="Prints active profile information. Workspace ID is not required when you want to only print active profile information.",
)
@click.pass_context
def configure(
    ctx: click.Context,
    workspace_id: str,
    tenant_id: Optional[str] = None,
    show: bool = False,
):
    version_checker = get_version_checker(ctx, interactive=True)

    if show and not workspace_id:
        bonsai_config = Config(use_aad=False)

        print_profile_information(bonsai_config)
    else:
        if not workspace_id:
            raise_as_click_exception("Workspace ID is required")

        cache_file = get_aad_cache_file()

        if os.path.exists(cache_file):
            os.remove(cache_file)

        bonsai_config = Config(use_aad=True)

        args = {
            "workspace_id": workspace_id,
            "tenant_id": tenant_id,
            "url": "https://cp-api.bons.ai",
            "gateway_url": "https://api.bons.ai",
        }

        if bonsai_config.update(**args):
            click.echo("Successfully configured")
        else:
            click.echo("Failed to configure")

        if show:
            print_profile_information(bonsai_config)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.command("switch", short_help="Switch profile.", hidden=True)
@click.argument("profile", required=False)
@click.option("--workspace-id", "-wid", help="Workspace ID.")
@click.option("--tenant-id", "-tid", help="Tenant ID.")
@click.option("--url", "-u", default=None, help="Set the brain api url.")
@click.option("--gateway-url", "-g", default=None, help="Set the brain gateway url.")
@click.option("--show", "-s", is_flag=True, help="Prints active profile information")
@click.pass_context
def switch(
    ctx: click.Context,
    profile: str,
    workspace_id: Optional[str],
    tenant_id: Optional[str],
    url: Optional[str],
    gateway_url: Optional[str],
    show: bool,
):
    """
    Change the active configuration section.\n
    For new profiles you must provide a url with the --url option.
    """
    version_checker = get_version_checker(ctx, interactive=True)

    config = Config(argv=sys.argv, use_aad=False)
    # `bonsai switch` and `bonsai switch -h/--help have the same output
    if not profile and not show:
        help_message: str = ctx.get_help()
        click.echo(message=help_message)
        list_profiles(config)
        ctx.exit(0)

    if not profile and show:
        print_profile_information(config)
        ctx.exit(0)

    # Let the user know that when switching to a new profile
    # the --workspace-id, --tenant-id, --url and --gateway_url options must be provided
    section_exists = config.has_section(profile)
    if not section_exists:
        error_msg = "\nProfile not found."
        required_options_provided = True

        if not workspace_id:
            required_options_provided = False
            error_msg += "\nPlease provide a workspace id with the --workspace-id option for new profiles"

        if not url:
            required_options_provided = False
            error_msg += "\nPlease provide a url with the --url option for new profiles"

        if not gateway_url:
            required_options_provided = False
            error_msg += "\nPlease provide a gateway url with the --gateway-url option for new profiles"

        if not required_options_provided:
            click.echo(error_msg)
            ctx.exit(1)

    config.update(profile=profile)

    if workspace_id:
        config.update(workspace_id=workspace_id)

    if tenant_id:
        config.update(tenant_id=tenant_id)

    if url:
        config.update(url=url)

    if gateway_url:
        config.update(gateway_url=gateway_url)

    if show:
        print_profile_information(config)

    version_checker.check_cli_version(wait=True, print_up_to_date=False)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--version",
    "-v",
    is_flag=True,
    callback=_version_callback,
    help="Show the version and check if Bonsai is up to date.",
    expose_value=False,
    is_eager=True,
)
@click.option(
    "--sysinfo",
    "-s",
    is_flag=True,
    callback=_sysinfo,
    help="Show system information.",
    expose_value=False,
    is_eager=True,
)
@click.option("--timeout", "-t", type=int, help="Set timeout for CLI API requests.")
@click.option(
    "--enable-color/--disable-color",
    callback=_set_color,
    help="Enable/disable color printing.",
    expose_value=False,
    is_eager=True,
    default=None,
)
@click.option(
    "--disable-version-check",
    "-dv",
    is_flag=True,
    default=False,
    help="Flag to disable version checking when running commands.",
)
@click.pass_context
def cli(ctx: click.Context, timeout: int, disable_version_check: bool):
    """Command line interface for the Microsoft Bonsai Service."""
    if timeout:
        BonsaiAPI.timeout = timeout

    ctx.ensure_object(dict)
    ctx.obj["VERSION_CHECK"] = False if disable_version_check else True


@click.command("help")
@click.pass_context
def bonsai_help(ctx: click.Context):
    """ Show this message and exit. """
    version_checker = get_version_checker(ctx, interactive=True)
    assert ctx.parent is not None
    click.echo(ctx.parent.get_help())
    version_checker.check_cli_version(wait=True, print_up_to_date=False)


cli.add_command(bonsai_help)
cli.add_command(brain)
cli.add_command(exportedbrain)
cli.add_command(simulator)
cli.add_command(switch)
cli.add_command(configure)


def main():
    cli()


if __name__ == "__main__":
    raise RuntimeError("run ../../bonsai.py instead.")
