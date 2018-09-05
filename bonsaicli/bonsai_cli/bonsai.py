"""
This file contains the main code for bonsai command line, a script
that can be run to interact with braind in place of Mastermind.

The `main` function in this file will be an entry point for execution
as specified by setup.py.
"""
import os
import pip
import platform
import pprint
import sys
import time
from json import decoder, dumps
from configparser import NoSectionError

import click
import requests
from tabulate import tabulate
from click._compat import get_text_stderr

from bonsai_ai import Config
from bonsai_ai.logger import Logger
from bonsai_cli.api import BonsaiAPI, BrainServerError
from bonsai_cli import __version__
from bonsai_cli.dotbrains import DotBrains
from bonsai_cli.projfile import ProjectDefault
from bonsai_cli.projfile import (
    ProjectFile, ProjectFileInvalidError, FileTooLargeError)


# Use input with Python3 and raw_input with Python2
prompt_user = input
if sys.version[0] == '2':
    prompt_user = raw_input

log = Logger()

""" Global variable for click context settings following the conventions
from the click documentation. It can be modified to add more context
settings if they are needed in future development of the cli.
"""
CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])


class CustomClickException(click.ClickException):
    """ Custom click exception that prints exceptions in color """
    def __init__(self, message, color):
        click.ClickException.__init__(self, message)
        self.color = color

    def show(self, file=None):
        """ Override ClickException function show() to print in color """
        if file is None:
            file = get_text_stderr()

        if self.color:
            click.secho(
                'ERROR: %s' % self.format_message(), file=file, fg='red')
        else:
            click.echo('ERROR: %s' % self.format_message(), file=file)


def _verify_required_configuration(bonsai_config):
    """This function verifies that the user's configuration contains
    the information required for interacting with the Bonsai BRAIN api.
    If required configuration is missing, an appropriate error is
    raised as a ClickException.
    """
    messages = []
    missing_config = False

    if not bonsai_config.accesskey:
        messages.append("Your access key is not configured.")
        missing_config = True

    if not bonsai_config.username:
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
    try:
        config = Config()
        color = config.use_color
    except ValueError:
        color = False

    if args and len(args) == 1:
        if isinstance(args[0], BrainServerError):
            raise CustomClickException(str(args[0]), color=color)
        else:
            raise CustomClickException('An error occurred\n'
                                       'Details: {}'.format(str(args[0])),
                                       color=color)
    elif args and len(args) > 1:
        raise CustomClickException("{}\nDetails: {}".format(args[0], args[1]),
                                   color=color)
    else:
        raise CustomClickException("An error occurred", color=color)


def _api():
    """
    Convenience function for creating and returning an API object.
    :return: An API object.
    """
    bonsai_config = Config()
    _verify_required_configuration(bonsai_config)
    return BonsaiAPI(access_key=bonsai_config.accesskey,
                     user_name=bonsai_config.username,
                     api_url=bonsai_config.url,
                     ws_url=bonsai_config._websocket_url(),
                     )


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


def _add_or_default_brain(directory, brain_name):
    """
    Verifies that a .brains file exists for given brain_name.
    Will create .brains file if it doesn't exist
    :param directory: Path to check/create .brains at
    :param brain_name: BRAIN name to set as default
    :param json: json flag from function that calls _add_or_default_brain
    """
    db = DotBrains(directory)
    brain = db.find(brain_name)
    if brain is None:
        log.debug("Adding {} to '.brains', added".format(brain_name))
        db.add(brain_name)
    else:
        db.set_default(brain)
        log.debug("Brain {} is in '.brains'.".format(brain_name))


def _check_dbrains(project=None):
    """ Utility function to check if the dbrains file has been
        modified. A valid dbrains file is in proper json format
    """
    try:
        if project:
            pf = ProjectFile.from_file_or_dir(project)
            db = DotBrains(pf.directory())
        else:
            db = DotBrains()
    except ValueError as err:
        if project:
            file_location = DotBrains.find_file(os.path.dirname(project))
        else:
            file_location = DotBrains.find_file(os.getcwd())
        msg = "Bonsai Command Failed." \
              "\nFailed to load .brains file '{}'".format(file_location)
        _raise_as_click_exception(msg, err)


def _show_version():
    click.echo("bonsai_cli %s" % __version__)


def _get_pypi_version(pypi_url):
    """
    This function attempts to get the package information
    from PyPi. It returns None if the request is bad, json
    is not decoded, or we have a KeyError in json dict
    """
    try:
        pkg_request = requests.get(pypi_url)
        pkg_json = pkg_request.json()
        pypi_version = pkg_json['info']['version']
    except requests.exceptions.RequestException:
        # could not connect to the server
        # blanket exception that covers various request issues
        return None
    except (decoder.JSONDecodeError, KeyError):
        # could not decode json or key error in dict
        return None

    # Successfully connected and obtained version info
    return pypi_version


def _check_version(ctx, param, value):
    """
    This is the callback function when --version option
    is used. The function lets the user know what version
    of the cli they are currently on and if there is an
    update available.
    """
    if not value or ctx.resilient_parsing:
        return

    pypi_url = 'https://pypi.python.org/pypi/bonsai-cli/json'
    pypi_version = _get_pypi_version(pypi_url)
    user_cli_version = __version__

    if not pypi_version:
        click.echo('Bonsai ' + user_cli_version)
        click.echo(
            'Unable to connect to PyPi and determine if CLI is up to date.')
    elif user_cli_version != pypi_version:
        click.echo('Bonsai ' + user_cli_version)
        click.echo('Bonsai update available. The most recent version is : ' +
                   pypi_version)
        click.echo(
            'Upgrade via pip using \'pip install --upgrade bonsai-cli\'')
    else:
        click.echo('Bonsai ' + user_cli_version)
        click.echo('Everything is up to date.')

    ctx.exit()


def _sysinfo(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo("\nPlatform Information\n--------------------")
    click.echo(sys.version)
    click.echo(platform.platform())
    packages = pip.utils.get_installed_distributions()
    click.echo("\nPackage Information\n-------------------")
    click.echo(pprint.pformat(packages))
    _print_profile_information(Config())
    ctx.exit()


def _list_profiles(bonsai_config):
    """ Lists available profiles """
    profile = bonsai_config.profile
    click.echo("\nAvailable Profiles:")
    if profile == "DEFAULT":
        click.echo("  DEFAULT" + " (active)")
    else:
        click.echo("  DEFAULT")

    # Grab Profiles from bonsai config and list each one
    sections = bonsai_config._section_list()
    for section in sections:
        if section == profile:
            click.echo("  " + section + " (active)")
        else:
            click.echo("  " + section)


def _print_profile_information(bonsai_config):
    """ Print current active profile information """
    try:
        profile_info = bonsai_config._section_items(bonsai_config.profile)
    except NoSectionError as e:
        profile_info = bonsai_config._defaults().items()

    click.echo("\nProfile Information")
    click.echo("--------------------")
    for key, val in profile_info:
        click.echo(key + ": " + str(val))


def _set_color(ctx, param, value):
    """ Set use_color flag in bonsai config """
    if value is None or ctx.resilient_parsing:
        return

    config = Config()
    if value:
        config.use_color = value
        config._update(use_color=value)
    else:
        config.use_color = False
        config._update(use_color=False)
    ctx.exit()


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', is_flag=True, default=False,
              help='Enable verbose debugging output.')
@click.option('--version', is_flag=True, callback=_check_version,
              help='Show the version and check if Bonsai is up to date.',
              expose_value=False, is_eager=True)
@click.option('--sysinfo', is_flag=True, callback=_sysinfo,
              help='Show system information.',
              expose_value=False, is_eager=True)
@click.option('--timeout', type=int,
              help='Set timeout for CLI API requests.')
@click.option('--enable-color/--disable-color', callback=_set_color,
              help='Enable/disable color printing.',
              expose_value=False, is_eager=True, default=None)
def cli(debug, timeout):
    """Command line interface for the Bonsai Artificial Intelligence Engine.
    """
    if debug:
        log.set_enable_all(True)

    if timeout:
        BonsaiAPI.TIMEOUT = timeout


@click.command('help')
@click.pass_context
def bonsai_help(ctx):
    """ Show this message and exit. """
    click.echo(ctx.parent.get_help())


@click.group()
def brain():
    """Create, delete BRAINs."""
    pass


@click.command()
@click.option('--username', help='Provide username.')
@click.option('--access_key', help='Provide an access key.')
@click.option('--show', is_flag=True,
              help='Prints active profile information.')
def configure(username, access_key, show):
    """Authenticate with the BRAIN Server."""
    bonsai_config = Config()

    if not username:
        username = click.prompt("Username")

    if not access_key:
        if bonsai_config.url == 'https://api.bons.ai':
            key_url = 'https://beta.bons.ai/accounts/settings/key'
        else:
            key_url = bonsai_config.url + "/accounts/settings/key"
        access_key_message = ("You can get this access key from "
                              "{}").format(key_url)
        click.echo(access_key_message)
        access_key = click.prompt(
            "Access Key (typing will be hidden)", hide_input=True)

    click.echo("Validating access key...")
    api = BonsaiAPI(access_key=access_key, user_name=username,
                    api_url=bonsai_config.url)
    content = None

    try:
        content = api.validate()
    except BrainServerError as e:
        _raise_as_click_exception(e)
    bonsai_config._update(accesskey=access_key,
                          username=username,
                          url=bonsai_config.url,
                          use_color=bonsai_config.use_color)

    click.echo("Success!")

    if show:
        _print_profile_information(bonsai_config)


@click.command()
@click.pass_context
@click.argument("profile", required=False)
@click.option("--url", default=None, help="Set the brain api url.")
@click.option('--show', is_flag=True,
              help="Prints active profile information")
@click.option("--help", "-h", "help_option", is_flag=True,
              help="Show this message and exit.")
def switch(ctx, profile, url, show, help_option):
    """
    Change the active configuration section.\n
    For new profiles you must provide a url with the --url option.
    """
    bonsai_config = Config(argv=sys.argv[0])
    # `bonsai switch` and `bonsai switch -h/--help have the same output
    if (not profile and not show) or help_option:
        click.echo(ctx.get_help())
        _list_profiles(bonsai_config)
        ctx.exit(0)

    if not profile and show:
        _print_profile_information(bonsai_config)
        ctx.exit(0)

    # Let the user know that when switching to a new profile
    # the --url option must be provided
    section_exists = bonsai_config._has_section(profile)
    if not section_exists and not url:
        error_msg = ('Profile not found.\n'
                     'Please provide a url with the --url '
                     'option for new profiles')
        click.echo(error_msg)
        ctx.exit(1)

    bonsai_config._update(profile=profile)
    if url:
        bonsai_config._update(url=url)

    url = bonsai_config.url
    click.echo("Success! Switched to {}. "
               "Commands will target: {}".format(profile, url))
    if show:
        _print_profile_information(bonsai_config)


@click.group()
def sims():
    """Retrieve information about simulators."""
    pass


@click.command("list", short_help="Lists BRAINs owned by current user.")
@click.option('--json', default=False, is_flag=True,
              help='Output json.')
def brain_list(json):
    """Lists BRAINs owned by current user."""
    try:
        content = _api().list_brains()
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if json:
        click.echo(dumps(content, indent=4, sort_keys=True))
    else:
        rows = []
        if content and 'brains' in content and len(content['brains']) > 0:
            # Try grabbing the default brain from .brains for later marking
            # If none is available, we just won't mark a list item
            try:
                default_brain = _default_brain()
            except:
                default_brain = ''

            for item in content['brains']:
                try:
                    name = item['name']
                    if name == default_brain:
                        name = click.style(name + "*", bold=True)
                        state = click.style(item['state'], bold=True)
                    else:
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


def brain_create_server(brain_name, project_file=None,
                        project_type=None, json=None):
    brain_exists = None
    try:
        brain_exists = _api().get_brain_exists(brain_name)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if brain_exists:
        click.echo("Brain {} exists.".format(brain_name))
        click.echo("Run \'bonsai push\' to push new inkling"
                   " and training source into {}".format(brain_name))
    else:
        try:
            if project_type:
                response = _api().create_brain(brain_name,
                                               project_type=project_type)
            elif project_file:
                response = _api().create_brain(brain_name,
                                               project_file=project_file)
            else:
                # TODO: Dead code that is never reached in the logic
                # TODO: Leaving it as it is part of the function signature
                response = _api().create_brain(brain_name)
        except BrainServerError as e:
            _raise_as_click_exception(e)

        if json:
            click.echo(dumps(response, indent=4, sort_keys=True))


def _is_empty_dir(dir):
    for file_or_dir in os.listdir(dir):
        if file_or_dir.startswith("."):
            # Omit .brains, .gitignore, etc.
            pass
        else:
            return False
    return True


def _brain_create_err_msg(project):
    """ Returns a string containing an error message
        that points to the appropriate project file """

    return "Bonsai Create Failed.\nFailed to load project file '{}'".format(
            ProjectFile.find(os.path.dirname(project)) if project
            else ProjectFile.find(os.getcwd()))


@click.command("create",
               short_help="Create a BRAIN and set the default BRAIN.")
@click.pass_context
@click.argument("brain_name", default='', required=True)
@click.option("--project",
              help='Override to target another project directory.')
@click.option("--project-type",
              help='Specify to download and use demo/starter project files '
                   '(e.g. "demos/cartpole").')
@click.option('--json', default=False, is_flag=True,
              help='Output json.')
def brain_create_local(ctx, brain_name, project, project_type, json):
    """Creates a BRAIN and sets the default BRAIN for future commands."""
    # TODO: Consider refactoring this function.
    # TODO: Logic is starting to get convuluted.
    _check_dbrains(project)

    # if the brain_name was left blank, try to pull one from .brains
    # if none available, raise UsageError and abort
    if brain_name == '':
        default = DotBrains().get_default()
        if default is None:
            raise click.UsageError(ctx.get_usage())
        else:
            brain_name = default.name

    if project_type:
        # Create brain using project_type.

        # Make sure clean directory before continuing.
        cur_dir = os.getcwd()
        if not _is_empty_dir(cur_dir):
            message = ("Refusing to create and download project files "
                       "using project-type in non-empty directory. "
                       "Please run in an empty directory.")
            raise click.ClickException(message)

        brain_create_server(brain_name, project_type=project_type, json=json)
        _brain_download(brain_name, cur_dir)
        try:
            bproj = ProjectFile.from_file_or_dir(cur_dir)
        except ValueError as e:
            err_msg = _brain_create_err_msg(project)
            _raise_as_click_exception(err_msg, e)
    else:
        # Create brain using project file.
        try:
            if project:
                bproj = ProjectFile.from_file_or_dir(project)
            else:
                bproj = ProjectFile()
        except ValueError as e:
            err_msg = _brain_create_err_msg(project)
            _raise_as_click_exception(err_msg, e)

        try:
            _validate_project_file(bproj)
        except FileTooLargeError as e:
            _raise_as_click_exception("Bonsai Create Failed.\n " + e.message)

        brain_create_server(brain_name, project_file=bproj, json=json)

    _add_or_default_brain(bproj.directory(), brain_name)
    ProjectDefault.apply(bproj)
    bproj.save()


@click.command("delete",
               short_help="Delete a BRAIN.")
@click.argument("brain_name")
def brain_delete(brain_name):
    """
    Deletes a BRAIN. A deleted BRAIN cannot be recovered.
    The name of a deleted BRAIN cannot be reused.
    This operation has no effect on your local file system.
    Deletion may cause discontinuity between .brains and the Bonsai platform.
    """
    try:
        brain_list = _api().list_brains()
        brains = brain_list['brains']
    except BrainServerError as e:
        _raise_as_click_exception(e)

    names = [b['name'] for b in brains]
    if brain_name not in names:
        _raise_as_click_exception(
                   "Brain {} does not exist. "
                   "No action was taken.".format(brain_name))
    else:
        try:
            _api().delete_brain(brain_name)
        except BrainServerError as e:
            _raise_as_click_exception(e)


@click.command("push")
@click.option("--brain",
              help="Override to target another BRAIN.")
@click.option("--project",
              help="Override to target another project directory")
@click.option('--json', default=False, is_flag=True,
              help='Output json.')
def brain_push(brain, project, json):
    """Uploads project file(s) to a BRAIN."""
    _check_dbrains(project)
    brain = _brain_fallback(brain, project)
    directory = project if project else os.getcwd()

    # Load project file.
    path = ProjectFile.find(directory)
    log.debug("Reading project file {}".format(path))
    if not path:
        message = ("Unable to locate project file (.bproj) in "
                   "directory={}".format(directory))
        raise click.ClickException(message)

    try:
        bproj = ProjectFile(path=path)
    except ValueError as e:
        msg = "Bonsai Push Failed.\nFailed to load project file '{}'".format(
            path)
        _raise_as_click_exception(msg, e)

    try:
        _validate_project_file(bproj)
    except FileTooLargeError as e:
        msg = "Bonsai Push Failed.\n " + e.message
        _raise_as_click_exception(msg)

    if not json:
        # Do not print output if json option is used
        files = list(bproj._list_paths()) + [bproj.project_path]
        click.echo("Uploading {} file(s) to {}... ".format(len(files), brain))
        log.debug("Uploading files={}".format(files))

    try:
        status = _api().get_brain_status(brain)
    except BrainServerError as e:
        _raise_as_click_exception(e)
    if status['state'] == 'In Progress':
        _raise_as_click_exception(
            "Can't push while training. Please stop training first.")

    try:
        response = _api().edit_brain(brain, bproj)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if json:
        click.echo(dumps(response, indent=4, sort_keys=True))
    else:
        try:
            _check_inkling(response["ink_compile"], bproj.inkling_file)
        except ProjectFileInvalidError as err:
            _raise_as_click_exception(err)

        num_files = len(response["files"])
        click.echo("Push succeeded. {} updated with {} files.".format(
            brain, num_files))
        for file in response["files"]:
            click.echo("{}".format(file))


def _validate_project_file(project_file):
    """ Sends error message to user if project file invalid. """
    try:
        project_file.validate_content()
    except ProjectFileInvalidError as e:
        _raise_as_click_exception(e)


def _check_inkling(inkling_info, inkling_file):
    """ Prints inkling errors/warnings """
    errors = inkling_info['errors']
    warnings = inkling_info['warnings']
    if errors or warnings:
        click.echo("\n{} Errors, {} Warnings in {}".
                   format(len(errors), len(warnings), inkling_file))
        _print_inkling_errors_or_warnings(errors + warnings)


def _print_inkling_errors_or_warnings(errors_or_warnings):
    """ Helper function for printing inkling errors and/or warnings """
    for key in errors_or_warnings:
        click.echo("{} {} (line {}, column {})".
                   format(key['code'], key['text'], key['line'],
                          key['column']))
    click.echo()


@click.command("pull", help="Downloads project file(s) from a BRAIN.")
@click.option("--all", is_flag=True,
              help="Option to pull all files from targeted BRAIN.")
@click.option("--brain", help="Override to target another BRAIN.")
def brain_pull(all, brain):
    """Pulls files related to the default BRAIN or the
       BRAIN provided by the option."""
    _check_dbrains()
    target_brain = brain if brain else _default_brain()

    try:
        click.echo("Pulling files from {}...".format(target_brain))
        files = _api().get_brain_files(brain_name=target_brain)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if not all:
        files = _user_select(files)
    _pull(files)


def _pull(files):
    """Pulls all files when all flag is used on brain_pull"""
    # Save all files user wants to pull
    for filename in files:
        click.echo("Pulling \"{}\"".format(filename))
        with open(filename, "wb") as outfile:
            outfile.write(files[filename])

    if len(files.keys()):
        click.echo("Success! {} files were downloaded from the server."
                   .format(len(files.keys())))
    else:
        click.echo("No files were downloaded from the server.")


def _user_select(files):
    """Prompts user if they want to pull a file and returns
        the ones that they want to pull"""
    yes = {'yes', 'y'}
    no = {'no', 'n'}
    user_selected_files = {}
    for filename in files:
        user_input = prompt_user("Do you want to pull \"{}\"? [Y/n]: "
                                 .format(filename)).lower()

        # Keep looping until a proper response is given
        while user_input not in yes and user_input not in no:
            user_input = prompt_user("Please enter Yes/y or No/n: ").lower()

        # Copy the user selected files to a new dict
        if user_input in yes:
            user_selected_files[filename] = files[filename]
    log.debug('Selected files {}: '.format(user_selected_files))
    return user_selected_files


@click.command("download")
@click.argument("brain_name")
def brain_download(brain_name):
    """Downloads all the files related to a BRAIN."""
    _check_dbrains()
    _brain_download(brain_name, brain_name)

    _add_or_default_brain(brain_name, brain_name)

    click.echo(("Download request succeeded. "
                "Files saved to directory '{}'".format(brain_name)))


def _brain_download(brain_name, dest_dir):
    if os.path.exists(dest_dir) and not _is_empty_dir(dest_dir):
        err_msg = ("Directory '{}' already exists and "
                   "is not an empty directory".format(dest_dir))
        _raise_as_click_exception(err_msg)

    try:
        click.echo("Downloading files...")
        files = _api().get_brain_files(brain_name=brain_name)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    with click.progressbar(files,
                           bar_template='%(label)s %(info)s',
                           label="Saving files...",
                           item_show_func=lambda x: x,
                           show_eta=False,
                           show_pos=True) as files_wrapper:
        for filename in files_wrapper:
            # respect directories
            file_path = os.path.join(dest_dir, filename)
            dirname = os.path.dirname(file_path)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)

            with open(file_path, "wb") as outfile:
                outfile.write(files[filename])


@click.group("train", short_help="Start and stop training on a BRAIN.")
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
@click.option('--json', default=False, is_flag=True,
              help='Output json.')
def sims_list(brain, project, json):
    """List the simulators connected to the BRAIN server."""
    _check_dbrains(project)
    brain = _brain_fallback(brain, project)

    try:
        content = _api().list_simulators(brain)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if json:
        click.echo(dumps(content, indent=4, sort_keys=True))
    else:
        try:
            click.echo("Simulators for {}:".format(brain))
            rows = []
            for sim_name, sim_details in content.items():
                rows.append([sim_name, 1, 'connected'])

            table = tabulate(rows,
                             headers=['NAME', 'INSTANCES', 'STATUS'],
                             tablefmt='simple')
            click.echo(table)
        except AttributeError as e:
            err_msg = 'You have not started training.\n' \
                        'Please run \'bonsai train start\' first.'
            click.echo(err_msg)


@click.command("start")
@click.option("--brain",
              help="Override to target another BRAIN.")
@click.option("--project",
              help='Override to target another project directory.')
@click.option("--remote", 'sim_local', flag_value=False, default=True,
              help='Run a simulator remotely on Bonsai\'s servers.')
@click.option('--json', default=False, is_flag=True,
              help='Output json.')
def brain_train_start(brain, project, sim_local, json):
    """Trains the specified BRAIN."""
    _check_dbrains(project)
    brain = _brain_fallback(brain, project)

    try:
        log.debug('Getting status for BRAIN: {}'.format(brain))
        status = _api().get_brain_status(brain)
    except BrainServerError as e:
        _raise_as_click_exception(e)
    if status['state'] == 'Error':
        _raise_as_click_exception(
            "Unable to start training because the brain "
            "is in an Error state. Please contact Bonsai Support. "
            "Visit http://bons.ai/contact-us for more "
            "information on how to contact us.")

    try:
        log.debug('Starting training for BRAIN: {}'.format(brain))
        content = _api().start_training_brain(brain, sim_local)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if json:
        log.debug('Outputting JSON')
        click.echo(dumps(content, indent=4, sort_keys=True))
    else:
        try:
            log.debug(
                "When training completes, connect simulators to {}{} "
                "for predictions".format(
                    Config()._websocket_url(),
                    content["simulator_predictions_url"]))
        except KeyError:
            pass


@click.command("status")
@click.option("--brain", help="Override to target another BRAIN.")
@click.option('--json', default=False, is_flag=True,
              help='Output json.')
@click.option("--project",
              help='Override to target another project directory.')
def brain_train_status(brain, json, project):
    """Gets training status on the specified BRAIN."""
    _check_dbrains(project)
    brain = _brain_fallback(brain, project)
    status = None
    try:
        log.debug('Getting status for BRAIN: {}'.format(brain))
        status = _api().get_brain_status(brain)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if json:
        log.debug('Outputting JSON')
        click.echo(dumps(status, indent=4, sort_keys=True))
    else:
        click.echo("Status for {}:".format(brain))
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
@click.option('--json', default=False, is_flag=True,
              help='Output json.')
def brain_train_stop(brain, project, json):
    """Stops training on the specified BRAIN."""
    _check_dbrains(project)
    brain = _brain_fallback(brain, project)
    try:
        log.debug('Stopping training for BRAIN: {}'.format(brain))
        content = _api().stop_training_brain(brain)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    log.debug('Stopped training')
    if json:
        log.debug('Outputting JSON')
        click.echo(dumps(content, indent=4, sort_keys=True))


@click.command("resume")
@click.option("--brain",
              help="Override to target another BRAIN")
@click.option("--project",
              help='Override to target another project directory.')
@click.option("--remote", 'sim_local', flag_value=False, default=True,
              help='Resume simulator remotely on Bonsai\'s servers.')
@click.option("--json", default=False, is_flag=True,
              help="Output json.")
def brain_train_resume(brain, project, sim_local, json):
    """Resume training on the specified BRAIN."""
    _check_dbrains(project)
    brain = _brain_fallback(brain, project)
    try:
        log.debug('Resuming training for BRAIN: {}'.format(brain))
        content = _api().resume_training_brain(brain, 'latest', sim_local)
    except BrainServerError as e:
        _raise_as_click_exception(e)

    if json:
        log.debug('Outputting JSON')
        click.echo(dumps(content, indent=4, sort_keys=True))
    else:
        try:
            log.debug(
                "When training completes, connect simulators to {}{} "
                "for predictions".format(
                    Config()._websocket_url(),
                    content["simulator_predictions_url"]))
        except KeyError:
            pass


# Compose the commands defined above.
# The top level commands: configure, sims and switch
cli.add_command(configure)
cli.add_command(sims)
cli.add_command(switch)
cli.add_command(bonsai_help)
# T1666 - break out the actions of brain_create_local
# cli.add_command(brain)

# The brain commands: create, list, download, load, and train
cli.add_command(brain_create_local)
cli.add_command(brain_delete)
cli.add_command(brain_push)
cli.add_command(brain_pull)
cli.add_command(brain_list)
cli.add_command(brain_download)
cli.add_command(brain_train)

# This sims command has one sub command: list
sims.add_command(sims_list)

# The brain train command has three sub commands: start, status, and stop
brain_train.add_command(brain_train_start)
brain_train.add_command(brain_train_status)
brain_train.add_command(brain_train_stop)
brain_train.add_command(brain_train_resume)


def main():
    if os.environ.get('STAGE') == 'dev':
        # Pause while brain gets ready... not necessary in other environments
        time.sleep(3)

    cli()


if __name__ == '__main__':
    raise RuntimeError("run ../bonsai.py instead.")
