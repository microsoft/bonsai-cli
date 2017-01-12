"""
This file contains the main code for bonsai command line, a script
that can be run to interact with braind in place of Mastermind.

The `main` function in this file will be an entry point for execution
as specified by setup.py.
"""
import os
import time
import logging

import click
from tabulate import tabulate

from bonsai_config import BonsaiConfig
from bonsai_cli.api import BonsaiAPI, BrainServerError
from bonsai_cli import __version__


def _verify_required_configuration(bonsai_config):
    """This function verifies that the user's configuration contains
    the information required for interacting with the Bonsai BRAIN api.
    If required configuration is missing, an appropriate error is
    raised as a ClickException.
    """
    messages = []
    missing_config = False

    if not bonsai_config.access_key():
        messages.append("Your access key is not configured.")
        missing_config = True

    if not bonsai_config.username():
        messages.append("Your username is not confgured.")
        missing_config = True

    if missing_config:
        messages.append(
            "Run 'bonsai configure' to update required configuration.")
        raise click.ClickException("\n".join(messages))


def _raise_as_click_exception(*args):
    """This function raises a ClickException with a message that contains
    the specified message and the details of the specified exception.
    This is useful for all of our commands to raise errors to the
    user in a consistent way.

    This function expects to be handed a BrainServerError, an Exception (or
    one of its subclasses), or a message string followed by an Exception.
    """
    if args and len(args) == 1:
        if isinstance(args[0], BrainServerError):
            raise click.ClickException(str(args[0]))
        else:
            raise click.ClickException('An error occurred\n'
                                       'Details: {}'.format(str(args[0])))
    elif args and len(args) > 1:
        raise click.ClickException("{}\nDetails: {}".format(args[0], args[1]))
    else:
        raise click.ClickException("An error occurred")


def _api():
    """
    Convenience function for creating and returning an API object.
    :return: An API object.
    """
    bonsai_config = BonsaiConfig()
    _verify_required_configuration(bonsai_config)
    return BonsaiAPI(access_key=bonsai_config.access_key(),
                     user_name=bonsai_config.username(),
                     api_url=bonsai_config.brain_api_url())


def _show_version():
    click.echo("bonsai_cli %s" % __version__)


@click.group(invoke_without_command=True)
@click.option('--debug/--no-debug', default=False,
              help='Enable/disable verbose debugging output.')
@click.option('--version', is_flag=True,
              help='Show the program version and exit.')
@click.pass_context
def cli(ctx, debug, version):
    """Command line interface for the Bonsai Artificial Intelligence Engine.
    """
    log_level = logging.DEBUG if debug else logging.ERROR
    logging.basicConfig(level=log_level)

    if ctx.invoked_subcommand is None:
        if version:
            _show_version()
        else:
            click.echo(ctx.get_help())


@click.group()
def brain():
    """Create, load, train BRAINs."""
    pass


@click.command()
@click.option('--key', help='Provide an access key.')
def configure(key):
    """Authenticate with the BRAIN Server."""
    bonsai_config = BonsaiConfig()

    if key:
        access_key = key
    else:
        access_key_message = ("You can get this access key from your "
                              "Account Settings page on the bonsai website")
        click.echo(access_key_message)

        access_key = click.prompt(
            "Access Key (typing will be hidden)", hide_input=True)

    click.echo("Validating access key...")
    api = BonsaiAPI(access_key=access_key, user_name=None,
                    api_url=bonsai_config.brain_api_url())
    content = None

    try:
        content = api.validate()
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if 'username' not in content:
        raise click.ClickException("Server did not return a username for "
                                   "access key {}".format(access_key))
    username = content['username']
    bonsai_config.update_access_key_and_username(access_key, username)

    click.echo("Success! Your username is {}".format(username))


@click.command()
@click.argument("profile")
@click.option("--url", default=None, help="Set the brain api url.")
def switch(profile, url):
    """Change the active configuration section. """
    bonsai_config = BonsaiConfig()
    bonsai_config.update(Profile=profile)
    if url:
        bonsai_config.update(Url=url)

    url = bonsai_config.brain_api_url()
    click.echo("Success! Switched to {}. "
               "Commands will target: {}".format(profile, url))


@click.group()
def sims():
    """Retrieve information about simulators."""
    pass


@click.command("list")
def brain_list():
    """Lists BRAINs owned by current user or by the user under a given
    URL.
    """
    try:
        content = _api().list_brains()
        rows = []
        if content and 'brains' in content and len(content['brains']) > 0:
            for item in content['brains']:
                try:
                    name = item['name']
                    state = item['state']
                    rows.append([name, state])
                except KeyError:
                    pass  # If it's missing a field, ignore it.
        if rows:
            table = tabulate(rows, headers=['BRAIN', 'State'],
                             tablefmt='fancy_grid')
            click.echo(table)
        else:
            click.echo('The current user has not created any brains.')
    except BrainServerError as e:
        _raise_as_click_exception(e)


@click.command("create")
@click.argument("brain_name")
def brain_create(brain_name):
    """Creates a BRAIN."""

    try:
        _api().create_brain(brain_name)
    except BrainServerError as e:
        _raise_as_click_exception(e)
    click.echo("Create request succeeded; a new brain was created.")


@click.command("load")
@click.argument("brain_name")
@click.argument("inkling_file")
def brain_load(brain_name, inkling_file):
    """Loads an inkling file into the specified BRAIN."""

    inkling_content = None
    try:
        # we could check if the file path ends in .ink here
        with open(inkling_file, 'r') as inkling_stream:
            inkling_content = inkling_stream.read()
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        _raise_as_click_exception(
            "Could not open '{}'".format(inkling_file), e)
    except UnicodeDecodeError as e:
        _raise_as_click_exception(
            "Could not read '{}', was it a .ink file?".format(inkling_file), e)

    try:
        content = _api().load_inkling_into_brain(brain_name=brain_name,
                                                 inkling_code=inkling_content)
        click.echo("Load request succeeded; a new brain version was created.")
        click.echo("Connect simulators to {}{} for training".format(
            BonsaiConfig().brain_websocket_url(),
            content["simulator_connect_url"]))
    except KeyError:
        click.echo("But missing the simulator connection path "
                   "the response.")
    except BrainServerError as e:
        _raise_as_click_exception(e)


@click.group("train")
def brain_train():
    """Start and stop training on a BRAIN, as well as get training
    status information.
    """
    pass


@click.command("list")
@click.argument("brain_name")
def sims_list(brain_name):
    """List the simulators connected to the BRAIN server."""

    try:
        content = _api().list_simulators(brain_name)
        rows = []
        for sim_name, sim_details in content.items():
            rows.append([sim_name, 1, 'connected'])

        table = tabulate(rows,
                         headers=['NAME', 'INSTANCES', 'STATUS'],
                         tablefmt='fancy_grid')
        click.echo(table)
    except BrainServerError as e:
        _raise_as_click_exception(e)


@click.command("start")
@click.argument("brain_name")
def brain_train_start(brain_name):
    """Trains the specified BRAIN."""
    try:
        content = _api().start_training_brain(brain_name)
        click.echo(
            "When training completes, connect simulators to {}{} "
            "for predictions".format(
                BonsaiConfig().brain_websocket_url(),
                content["simulator_predictions_url"]))
    except KeyError:
        pass
    except BrainServerError as e:
        _raise_as_click_exception(e)


@click.command("status")
@click.argument("brain_name")
@click.option('--json', default=False, is_flag=True,
              help='Output status as json')
def brain_train_status(brain_name, json):
    """Gets training status on the specified BRAIN."""

    status = None
    try:
        status = _api().get_brain_status(brain_name)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if json:
        click.echo(status)
    else:
        keys = list(status.keys())
        keys.sort()
        rows = ((k, status[k]) for k in keys)
        table = tabulate(rows,
                         headers=['KEY', 'VALUE'],
                         tablefmt='simple')
        click.echo(table)


@click.command("stop")
@click.argument("brain_name")
def brain_train_stop(brain_name):
    """Stops training on the specified BRAIN."""

    try:
        _api().stop_training_brain(brain_name)
        click.echo("Stopped.")
    except BrainServerError as e:
        _raise_as_click_exception(e)


# Compose the commands defined above.
# The top level commands: brain, configure, sims and switch
cli.add_command(brain)
cli.add_command(configure)
cli.add_command(sims)
cli.add_command(switch)

# The brain command has sub commands: create, list, load, and train
brain.add_command(brain_create)
brain.add_command(brain_list)
brain.add_command(brain_load)
brain.add_command(brain_train)

# This sims command has one sub command: list
sims.add_command(sims_list)

# The brain train command has three sub commands: start, status, and stop
brain_train.add_command(brain_train_start)
brain_train.add_command(brain_train_status)
brain_train.add_command(brain_train_stop)


def main():
    if os.environ.get('STAGE') == 'dev':
        # Pause while brain gets ready... not necessary in other environments
        time.sleep(3)

    cli()


if __name__ == '__main__':
    raise RuntimeError("run ../bonsai.py instead.")
