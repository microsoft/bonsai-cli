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
from bonsai_cli.dotbrains import DotBrains
from bonsai_cli.projfile import ProjectDefault
from bonsai_cli.projfile import ProjectFile, ProjectFileInvalidError


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


def _default_brain():
    """
    Look up the currently selected brain.
    :return: The default brain from the .brains file
    """
    dotbrains = DotBrains()
    brain = dotbrains.get_default()
    if brain is None:
        raise click.ClickException(
            "Missing brain name. Specify a name with `--brain NAME`.")
    return brain.name


def _brain_fallback(brain, project):
    """
    Implements the fallback options for brain name.
    If a brain is given directly, use it.
    If a project is specified, check that for a brain.
    If neither is given, use .brains locally.
    """
    if brain:
        return brain
    if project:
        pf = ProjectFile.from_file_or_dir(project)
        db = DotBrains(pf.directory())
        b = db.get_default()
        if b:
            return b.name
        else:
            raise click.ClickException(
                "No Brains found with the given project")
    return _default_brain()


def _show_version():
    click.echo("bonsai_cli %s" % __version__)


@click.group()
@click.option('--debug/--no-debug', default=False,
              help='Enable/disable verbose debugging output.')
@click.version_option(version=__version__)
def cli(debug):
    """Command line interface for the Bonsai Artificial Intelligence Engine.
    """
    log_level = logging.DEBUG if debug else logging.ERROR
    logging.basicConfig(level=log_level)


@click.group()
def brain():
    """Create, delete BRAINs."""
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
                             tablefmt='simple')
            click.echo(table)
        else:
            click.echo('The current user has not created any brains.')
    except BrainServerError as e:
        _raise_as_click_exception(e)


@click.command("create")
@click.argument("brain_name")
def brain_create(brain_name):
    """ Creates a BRAIN on the server."""
    brain_create_server(brain_name)


def brain_create_server(brain_name):
    try:
        brain_list = _api().list_brains()
        brains = brain_list['brains']
    except BrainServerError as e:
        click.echo("Error:")
        _raise_as_click_exception(e)

    names = [b['name'] for b in brains]
    if brain_name in names:
        click.echo("Brain {} exists.".format(brain_name))
    else:
        click.echo("Creating {}, ".format(brain_name), nl=False)
        try:
            _api().create_brain(brain_name)
        except BrainServerError as e:
            click.echo("error:")
            _raise_as_click_exception(e)
        else:
            click.echo("created.")


@click.command("create")
@click.argument("brain_name")
@click.option("--project",
              help='Override to target another project directory.')
def brain_create_local(brain_name, project):
    """Creates a BRAIN and sets the default BRAIN for future commands."""

    brain_create_server(brain_name)

    bproj = ProjectFile.from_file_or_dir(project) if project else ProjectFile()

    db = DotBrains(bproj.directory())
    brain = db.find(brain_name)
    if brain is None:
        click.echo("Adding {} to '.brains', ".format(brain_name), nl=False)
        db.add(brain_name)
        click.echo("added.")
    else:
        db.set_default(brain)
        click.echo("Brain {} is in '.brains'.".format(brain_name))

    ProjectDefault.apply(bproj)
    bproj.save()
    click.echo("Saving project file, saved.")
    click.echo("")
    click.echo("Run 'bonsai load' to load inkling and "
               "training sources into {}.".format(brain_name))


@click.command("load")
@click.option("--brain",
              help="Override to target another BRAIN.")
@click.option("--project",
              help='Override to target another project directory.')
def brain_load(brain, project):
    """Loads an inkling file into the given BRAIN."""

    brain = _brain_fallback(brain, project)
    bproj = ProjectFile.from_file_or_dir(project) if project else ProjectFile()
    inkling_content = None
    try:
        inkling_path = bproj.inkling_file
        inkling_path = os.path.join(bproj.directory(), inkling_path)
    except ProjectFileInvalidError as e:
        _raise_as_click_exception("Inkling Path Lookup", e)

    try:
        # we could check if the file path ends in .ink here
        with open(inkling_path, 'r') as inkling_stream:
            inkling_content = inkling_stream.read()
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        _raise_as_click_exception(
            "Could not open '{}'".format(inkling_path), e)
    except UnicodeDecodeError as e:
        _raise_as_click_exception(
            "Could not read '{}', was it a .ink file?".format(inkling_path), e)

    try:
        content = _api().load_inkling_into_brain(brain_name=brain,
                                                 inkling_code=inkling_content)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    click.echo("Load request succeeded; a new brain version was created.")
    try:
        click.echo("Connect simulators to {}{} for training".format(
            BonsaiConfig().brain_websocket_url(),
            content["simulator_connect_url"]))
    except KeyError:
        click.echo("But missing the simulator connection path in "
                   "the response.")


@click.group("train")
def brain_train():
    """Start and stop training on a BRAIN, as well as get training
    status information.
    """
    pass


@click.command("list")
@click.option("--brain",
              help="Override to target another BRAIN.")
@click.option("--project",
              help='Override to target another project directory.')
def sims_list(brain, project):
    """List the simulators connected to the BRAIN server."""

    brain = _brain_fallback(brain, project)
    try:
        content = _api().list_simulators(brain)
        rows = []
        for sim_name, sim_details in content.items():
            rows.append([sim_name, 1, 'connected'])

        table = tabulate(rows,
                         headers=['NAME', 'INSTANCES', 'STATUS'],
                         tablefmt='simple')
        click.echo(table)
    except BrainServerError as e:
        _raise_as_click_exception(e)


@click.command("start")
@click.option("--brain",
              help="Override to target another BRAIN.")
@click.option("--project",
              help='Override to target another project directory.')
def brain_train_start(brain, project):
    """Trains the specified BRAIN."""

    brain = _brain_fallback(brain, project)
    try:
        content = _api().start_training_brain(brain)
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
@click.option("--brain", help="Override to target another BRAIN.")
@click.option('--json', default=False, is_flag=True,
              help='Output status as json.')
@click.option("--project",
              help='Override to target another project directory.')
def brain_train_status(brain, json, project):
    """Gets training status on the specified BRAIN."""

    brain = _brain_fallback(brain, project)
    status = None
    try:
        status = _api().get_brain_status(brain)
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
@click.option("--brain",
              help="Override to target another BRAIN.")
@click.option("--project",
              help='Override to target another project directory.')
def brain_train_stop(brain, project):
    """Stops training on the specified BRAIN."""

    brain = _brain_fallback(brain, project)
    try:
        _api().stop_training_brain(brain)
        click.echo("Stopped.")
    except BrainServerError as e:
        _raise_as_click_exception(e)


# Compose the commands defined above.
# The top level commands: configure, sims and switch
cli.add_command(brain)
cli.add_command(configure)
cli.add_command(sims)
cli.add_command(switch)

# The brain commands: create, list, load, and train
cli.add_command(brain_create_local)
cli.add_command(brain_list)
cli.add_command(brain_load)
cli.add_command(brain_train)

# The brain sub commands: create
brain.add_command(brain_create)

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
