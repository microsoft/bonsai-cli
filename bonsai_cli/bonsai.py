"""
This file contains the main code for bonsai command line, a script
that can be run to interact with braind in place of Mastermind.

The `main` function in this file will be an entry point for execution
as specified by setup.py.
"""
import os
import requests
import time
import subprocess
import tempfile

import click
from tabulate import tabulate

from bonsai_config import BonsaiConfig


ACCESS_KEY_URL_TEMPLATE = "{web_url}/accounts/key"
VALIDATE_URL_TEMPLATE = "{web_url}/v1/validate"
LIST_BRAINS_URL_TEMPLATE = "{api_url}/v1/{username}"
CREATE_BRAIN_URL_TEMPLATE = "{api_url}/v1/{username}/brains"
LOAD_INK_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/ink"
SIMS_INFO_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/sims"
STATUS_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/status"
TRAIN_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/train"
STOP_URL_TEMPLATE = "{api_url}/v1/{username}/{brain}/stop"


# If installed, the program to run on GnuPlot for a two-X-axis plot.
_PLOT_2_PROGRAM = """
set term dumb
set timefmt '%Y-%m-%dT%H:%M:%SZ'
set title '{title}'
set xlabel '{x}'
set x2label 'Date/Time (UTC)'
set x2data time
set format x2 '%H:%MZ'
set xtics nomirror
set x2tics
plot '-' using 1:2, '-' using 1:2 axes x2y1
"""

# If installed, the program to run on GnuPlot for a one-X-axis plot.
_PLOT_1_PROGRAM = """
set term dumb
set timefmt '%Y-%m-%dT%H:%M:%SZ'
set title '{title}'
set format x '%H:%MZ'
set xlabel 'Date/Time (UTC)'
plot '-' using 1:2
"""


def _plot_time_series(data, title, gnuplot_path):
    """
    As an optional feature, if gnuplot is on the path, this makes ascii plots
    of the time series data present in the status endpoint.
    :param data: An array with the time series data from Bonsai BRAIN API.
    :param title: The title of the time series plot.
    :param gnuplot_path: Path to the gnuplot tool.
    :return: String containing an ASCII rendering of the time series plot.
    """
    if not data:
        return ''
    first_row = data[0]
    if len(first_row) not in [2, 3]:
        return ''

    program = None
    alt_x = None
    if len(first_row) == 3:
        keys = [i for i in data[0].keys()]
        keys.remove('time')
        keys.remove('value')
        alt_x = keys[0]
        program = _PLOT_2_PROGRAM.format(x=alt_x, title=title)
    else:
        program = _PLOT_1_PROGRAM.format(title=title)

    program_file = None
    with tempfile.NamedTemporaryFile(delete=False,
                                     mode='w') as outfile:
        outfile.write(program)
        if alt_x:
            for i in data:
                x_val = str(i[alt_x])
                value = str(i['value'])
                outfile.write('{}\t{}\n'.format(x_val, value))
        outfile.write('e\n')
        for i in data:
            timestamp = str(i['time'])
            value = str(i['value'])
            outfile.write('{}\t{}\n'.format(timestamp, value))

        program_file = outfile.name

    try:
        result = subprocess.check_output([gnuplot_path, program_file])
        return result
    except subprocess.CalledProcessError:
        return ''
    finally:
        os.remove(program_file)


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


def _raise_as_click_exception(message, exception):
    """This function raises a ClickException with a message that contains
    the specified message and the details of the specified exception.
    This is useful for all of our commands to raise errors to the
    user in a consistent way.
    """
    raise click.ClickException("{}\nDetails: {}".format(message, exception))


def _raise_for_status(response):
    """This function raises HTTP response errors to the user as a
    ClickException. It will include error details found in the response
    body if possible.
    """
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        try:
            message = "Request failed with error message '{}'.".format(
                response.json()["error"])
        except:
            message = "Request failed."
        _raise_as_click_exception(message, e)


@click.group()
def cli():
    """Command line interface for the Bonsai Artificial Intelligence Engine.
    """
    pass


@click.group()
def brain():
    """Create, load, train BRAINs."""
    pass


@click.command()
def configure():
    """Authenticate with the BRAIN Server."""
    bonsai_config = BonsaiConfig()

    access_key_path = ACCESS_KEY_URL_TEMPLATE.format(
        web_url=bonsai_config.brain_web_url())
    access_key_message = "You can get the access key at {}".format(
        access_key_path)
    click.echo(access_key_message)

    access_key = click.prompt(
        "Access Key (typing will be hidden)", hide_input=True)
    click.echo("Validating access key...")

    validate_path = VALIDATE_URL_TEMPLATE.format(
        web_url=bonsai_config.brain_web_url())
    click.echo("request to {}".format(validate_path))

    try:
        response = requests.post(
            validate_path,
            headers={'Authorization': access_key})
        _raise_for_status(response)

        content = response.json()
        if 'username' not in content:
            raise click.ClickException("Server did not return a username for "
                                       "access key {}".format(access_key))
        username = content['username']
        bonsai_config.update_access_key_and_username(access_key, username)

        click.echo("Success! Your username is {}".format(username))

    except requests.RequestException as e:
        _raise_as_click_exception(
            "Request to {} failed".format(e.request.url), e)


@click.group()
def sims():
    """Retrieve information about simulators"""
    pass


@click.command("list")
def brain_list():
    """Lists BRAINs owned by current user or by the user under a given
    URL.
    """
    bonsai_config = BonsaiConfig()
    _verify_required_configuration(bonsai_config)

    path = LIST_BRAINS_URL_TEMPLATE.format(
        api_url=bonsai_config.brain_api_url(),
        username=bonsai_config.username())

    try:
        click.echo("About to GET {} for list".format(path))

        response = requests.get(
            path, headers={'Authorization': bonsai_config.access_key()})
        _raise_for_status(response)

        try:
            content = response.json()
            if content and content['brains'] and len(content['brains']) > 0:
                rows = []
                for item in content['brains']:
                    name = item['name']
                    state = item['state']
                    rows.append([name, state])
                table = tabulate(rows, headers=['BRAIN', 'State'],
                                 tablefmt='fancy_grid')
                click.echo(table)
            else:
                click.echo('The current user has not created any brains.')
        except (ValueError, KeyError):
            pass

    except requests.RequestException as e:
        _raise_as_click_exception(
            "Request to {} failed".format(e.request.url), e)


@click.command("create")
@click.argument("brain_name")
def brain_create(brain_name):
    """Creates a BRAIN."""
    bonsai_config = BonsaiConfig()
    _verify_required_configuration(bonsai_config)

    path = CREATE_BRAIN_URL_TEMPLATE.format(
        api_url=bonsai_config.brain_api_url(),
        username=bonsai_config.username())

    json_body = {"name": brain_name}

    try:
        click.echo(
            "About to POST {} to create brain {}".format(path, brain_name))
        response = requests.post(
            path,
            json=json_body,
            headers={'Authorization': bonsai_config.access_key()})
        _raise_for_status(response)

        click.echo("Create request succeeded; a new brain was created.")

    except requests.RequestException as e:
        _raise_as_click_exception(
            "Request to {} failed".format(e.request.url), e)


@click.command("load")
@click.argument("brain_name")
@click.argument("inkling_file")
def brain_load(brain_name, inkling_file):
    """Loads an inkling file into the specified BRAIN."""
    bonsai_config = BonsaiConfig()
    _verify_required_configuration(bonsai_config)

    try:
        # we could check if the file path ends in .ink here
        with open(inkling_file, 'r') as inkling_content:
            json_body = {"ink_content": inkling_content.read()}
    except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
        _raise_as_click_exception(
            "Could not open '{}'".format(inkling_file), e)
    except UnicodeDecodeError as e:
        _raise_as_click_exception(
            "Could not read '{}', was it a .ink file?".format(inkling_file), e)

    path = LOAD_INK_URL_TEMPLATE.format(
        api_url=bonsai_config.brain_api_url(),
        username=bonsai_config.username(),
        brain=brain_name)

    try:
        click.echo("About to POST {} to load inkling".format(path))
        response = requests.post(
            path,
            json=json_body,
            headers={'Authorization': bonsai_config.access_key()})
        _raise_for_status(response)

        click.echo("Load request succeeded; a new brain version was created.")

        try:
            content = response.json()
            click.echo(
                "Connect simulators to {}{} for training.".format(
                    bonsai_config.brain_websocket_url(),
                    content["simulator_connect_path"]))
        except (ValueError, KeyError):
            pass

    except requests.RequestException as e:
        _raise_as_click_exception(
            "Request to {} failed".format(e.request.url), e)


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
    bonsai_config = BonsaiConfig()
    _verify_required_configuration(bonsai_config)

    path = SIMS_INFO_URL_TEMPLATE.format(
        api_url=bonsai_config.brain_api_url(),
        username=bonsai_config.username(),
        brain=brain_name)

    try:
        click.echo("About to GET {} for simulator information".format(path))

        response = requests.get(
            path, headers={'Authorization': bonsai_config.access_key()})
        _raise_for_status(response)

        try:
            content = response.json()
        except ValueError as e:
            # If there was no json in the response, something went
            # wrong with the API.
            _raise_as_click_exception(
                "Request succeeded, but the response did not contain "
                "valid json.", e)

    except requests.RequestException as e:
        _raise_as_click_exception(
            "Request to {} failed".format(e.request.url), e)

    max_sim_name_len = 0
    if content:
        max_sim_name_len = max(len(sim_name) for sim_name in content.keys())

    name_col_len = max(4, max_sim_name_len) + 3
    column_format = "{:" + str(name_col_len) + "}{:12}{}"

    click.echo(column_format.format("NAME", "INSTANCES", "STATUS"))
    for sim_name, sim_details in content.items():
        click.echo(column_format.format(sim_name, "1", "connected"))


@click.command("start")
@click.argument("brain_name")
def brain_train_start(brain_name):
    """Trains the specified BRAIN."""
    bonsai_config = BonsaiConfig()
    _verify_required_configuration(bonsai_config)

    path = TRAIN_URL_TEMPLATE.format(
        api_url=bonsai_config.brain_api_url(),
        username=bonsai_config.username(),
        brain=brain_name)

    try:
        click.echo("About to PUT {} for train".format(path))

        response = requests.put(
            path, headers={'Authorization': bonsai_config.access_key()})
        _raise_for_status(response)

        click.echo("Training started.")
        try:
            content = response.json()
            click.echo(
                "When training completes, connect simulators to {}{} "
                "for predictions".format(
                    bonsai_config.brain_websocket_url(),
                    content["simulator_predictions_url"]))
        except (ValueError, KeyError):
            pass

    except requests.RequestException as e:
        _raise_as_click_exception(
            "Request to {} failed".format(e.request.url), e)


@click.command("status")
@click.argument("brain_name")
def brain_train_status(brain_name):
    """Gets training status on the specified BRAIN."""
    bonsai_config = BonsaiConfig()
    _verify_required_configuration(bonsai_config)

    path = STATUS_URL_TEMPLATE.format(
        api_url=bonsai_config.brain_api_url(),
        username=bonsai_config.username(),
        brain=brain_name)

    click.echo("About to GET {} for status".format(path))

    try:
        response = requests.get(
            path, headers={'Authorization': bonsai_config.access_key()})
        _raise_for_status(response)

        status = response.json()
        training_state = status.get('state', '')

        if training_state == 'ready':
            click.echo('Ready for training')

        elif training_state == 'queued':
            click.echo('Scheduled for training')

        elif training_state == 'training':
            click.echo("Reward for episode {} was {}".format(
                status.get('episode', 0),
                float(status.get('score', 0))))

        elif training_state in ['deployed', 'ready_to_deploy']:
            click.echo('Training complete')

        else:
            click.echo('Brain state is: {}'.format(
                training_state))

    except requests.RequestException as e:
        _raise_as_click_exception(
            "Request to {} failed".format(e.request.url), e)


@click.command("stop")
@click.argument("brain_name")
def brain_train_stop(brain_name):
    """Stops training on the specified BRAIN."""
    bonsai_config = BonsaiConfig()
    _verify_required_configuration(bonsai_config)

    path = STOP_URL_TEMPLATE.format(
        api_url=bonsai_config.brain_api_url(),
        username=bonsai_config.username(),
        brain=brain_name)

    click.echo("About to PUT {} to stop training".format(path))

    try:
        response = requests.put(
            path, headers={'Authorization': bonsai_config.access_key()})
        _raise_for_status(response)

        click.echo('Stopped')

    except requests.RequestException as e:
        _raise_as_click_exception(
            "Request to {} failed".format(e.request.url), e)


# Compose the commands defined above.
# There are three top level commands: brain, configure, and sims
cli.add_command(brain)
cli.add_command(configure)
cli.add_command(sims)

# The brain command has three sub commands: list, load, and train
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
