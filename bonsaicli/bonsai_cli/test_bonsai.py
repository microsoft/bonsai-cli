"""
This file contains unit tests for bonsai command line.
"""
import os
from unittest import TestCase
from json import loads, dump
from shutil import copyfile

# python 3.3+ includes mock in the unittest module
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from contextlib import contextmanager
from click.testing import CliRunner

from bonsai_ai import Config
from bonsai_cli import __version__
from bonsai_cli.api import BrainServerError, BonsaiAPI
from bonsai_cli.bonsai import cli, _get_pypi_version
from bonsai_cli.dotbrains import DotBrains
from bonsai_cli.projfile import ProjectFile

SUCCESS_EXIT_CODE = 0
FAILURE_EXIT_CODE = 1
ACCESS_KEY = '00000000-1111-2222-3333-000000000001'
USERNAME = 'admin'

BONSAI_BACKUP = './bonsai.bak'


def _print_result(result):
    """Debugging method to print the output returned from click."""
    print(result.output)
    print(result.exception)
    import traceback
    traceback.print_tb(result.exc_info[2])


@contextmanager
def temp_filesystem(test_class):
    """ Context manager that wraps CliRunner.isolated_filesystem().
        It will set your $HOME directory to the temporary directory
        created by the isolated_filesystem context manager

        You must pass a class that has an instance of the CliRunner
        instantiated as `runner`. This is a common pattern in the cli tests.

        How to use:
            with temp_filesystem():
                YOUR CODE GOES HERE
    """
    with test_class.runner.isolated_filesystem():
        # Change $HOME to current temp directory
        temp_dir = os.getcwd()
        home_dir = os.environ["HOME"] if "HOME" in os.environ else ""
        os.environ["HOME"] = temp_dir

        # Code in the scope of the context manager runs here
        yield

        # restore $HOME variable
        os.environ["HOME"] = home_dir


class TestBrainCommand(TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_missing_access_key(self):
        with temp_filesystem(self):
            result = self.runner.invoke(cli, ['list'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

    def test_missing_parameter_create(self):
        with temp_filesystem(self):
            result = self.runner.invoke(cli, ['create'])
            self.assertNotEqual(result.exit_code, SUCCESS_EXIT_CODE)

    def test_missing_parameter_delete(self):
        with temp_filesystem(self):
            result = self.runner.invoke(cli, ['delete'])
            self.assertNotEqual(result.exit_code, SUCCESS_EXIT_CODE)


class TestMockedBrainCommand(TestCase):
    """ Tests for bonsai commands with api calls replaced by mocks
    """
    def setUp(self):
        self.runner = CliRunner()

        self.api = Mock()
        patcher = patch('bonsai_cli.bonsai._api',
                        new=Mock(return_value=self.api))

        self.addCleanup(patcher.stop)
        patcher.start()

    def _add_config(self):
        ACCESS_KEY = '00000000-1111-2222-3333-000000000001'
        USERNAME = 'admin'
        PROFILE = 'test'
        URL = 'http://testing'

        config = Config()
        config._update(profile=PROFILE, url=URL,
                       accesskey=ACCESS_KEY, username=USERNAME)

    def test_brain_download(self):
        self.api.get_brain_files.return_value = {
            'test.txt': b'# test file 1',
            'test2.txt': b'# test file 2'
        }

        with temp_filesystem(self):
            self._add_config()

            result = self.runner.invoke(
                cli, ['download', 'mybrain'])

            saved_files = os.listdir('mybrain')
            self.assertIn('test.txt', saved_files)
            self.assertIn('test2.txt', saved_files)

            repeat_response = self.runner.invoke(
                cli, ['download', 'mybrain'])

        self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
        # should fail if directory/files already exist
        self.assertEqual(repeat_response.exit_code, FAILURE_EXIT_CODE)

    def test_brain_download_invalid_dotbrains(self):
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['download', 'mybrain'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def test_brain_pull_all(self):
        """Test that brain pull all pulles all files"""
        self.api.get_brain_files.return_value = {
            'test.txt': b'# test file 1',
            'test2.txt': b'# test file 2'
        }

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            result = self.runner.invoke(cli, ['pull', '--all'])
            files = [f for f in os.listdir('.') if os.path.isfile(f)]
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue('test.txt' in files)
            self.assertTrue('test2.txt' in files)

    @patch('bonsai_cli.bonsai.prompt_user', return_value='yes')
    def test_brain_pull_yes(self, patched_input):
        """Test files are pulled when answering yes during bonsai pull"""
        self.api.get_brain_files.return_value = {
            'test.txt': b'# test file 1',
            'test2.txt': b'# test file 2'
        }

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            result = self.runner.invoke(cli, ['pull'])
            files = [f for f in os.listdir('.') if os.path.isfile(f)]
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue('test.txt' in files)
            self.assertTrue('test2.txt' in files)

    @patch('bonsai_cli.bonsai.prompt_user', return_value='no')
    def test_brain_pull_no(self, patched_input):
        """Test files are not pulled when answering no during bonsai pull"""
        self.api.get_brain_files.return_value = {
            'test.txt': b'# test file 1',
            'test2.txt': b'# test file 2'
        }

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            result = self.runner.invoke(cli, ['pull'])
            files = [f for f in os.listdir('.') if os.path.isfile(f)]
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertFalse('test.txt' in files)
            self.assertFalse('test2.txt' in files)

    def test_brain_pull_fail(self):
        """Test that brain pull fails with appropriate Error Message"""
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()

            result = self.runner.invoke(cli, ['pull'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('Error: Missing brain name' in result.output)

    def test_brain_pull_invalid_brains(self):
        """ Test that brain pull fails with invalid .brains file """
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['pull'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def test_brain_delete(self):
        with temp_filesystem(self):
            self._add_config()

            # Brain exists, delete succeeds
            brain_set = {'brains': [{'name': 'mybrain'}]}
            self.api.list_brains = Mock(return_value=brain_set)
            result = self.runner.invoke(
                cli, ['delete', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Brain does not exist, command completes but prints a
            # message informing user that no action was taken.
            brain_set = {'brains': []}
            self.api.list_brains = Mock(return_value=brain_set)
            result = self.runner.invoke(
                cli, ['delete', 'mybrain'])

            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue("WARNING" not in result.output)
            self.assertTrue("does not exist. No action" in result.output)

    def test_brain_create(self):
        self.api.get_brain_exists = Mock(return_value=False)
        with temp_filesystem(self):
            self._add_config()

            # Create brain and local file
            result = self.runner.invoke(
                cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Both already exist
            open('test.ink', 'a').close()
            open('test_simulator.py', 'a').close()
            brain_set = {'brains': [{'name': 'mybrain'}]}
            self.api.get_brain_exists = Mock(return_value=True)
            result = self.runner.invoke(
                cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Create only local file
            os.remove('.brains')
            result = self.runner.invoke(
                cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Create only remote brain
            self.api.get_brain_exists = Mock(return_value={'brains': []})
            db = DotBrains()
            db.add('mybrain2')
            result = self.runner.invoke(
                cli, ['create', 'mybrain2'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

    def test_brain_create_default_brain(self):
        self.api.get_brain_exists = Mock(return_value=False)
        with temp_filesystem(self):
            with open('.brains', 'w') as fd:
                dotbrains_dict = {
                    "brains": [
                        {"name": "mybrain",
                         "default": True}
                    ]
                }
                dump(dotbrains_dict, fd)
            result = self.runner.invoke(cli, ['create'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

    def test_brain_create_json_option(self):
        self.api.get_brain_exists = Mock(return_value=False)
        self.api.create_brain = Mock(return_value="{'brains': 'brains'}")
        with temp_filesystem(self):
            self._add_config()
            # Create brain and local file
            result = self.runner.invoke(
                cli, ['create', 'mybrain', '--json'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            # Throws error if not valid json
            loads(result.output)

    def test_brain_create_with_existing_project_file(self):
        def _side_effect_create_brain(brain, project_file=None,
                                      project_type=None):
            # Checks arguments for BonsaiAPI.edit_brain(..) """
            self.assertEqual(brain, "mybrain")
            self.assertTrue(project_file.exists())
            self.assertTrue('test.txt' in project_file.files)
            self.assertTrue('test2.txt' in project_file.files)

            # Checks payload/filesdata that will be sent.
            tempapi = BonsaiAPI(None, None, None)
            (payload, filesdata) = tempapi._payload_create_brain(brain,
                                                                 project_file)
            self._check_payload(payload, ["test.txt", "test2.txt"])
            self.assertDictEqual(filesdata, {"test.txt": b'test content',
                                             "test2.txt": b'test content 2'})
            self.assertTrue("name" in payload)
            return {}
        self.api.get_brain_exists = Mock(return_value=False)
        self.api.create_brain = Mock(side_effect=_side_effect_create_brain)

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            # Write some files.
            with open('test.txt', 'w') as f1:
                f1.write("test content")
            with open('test2.txt', 'w') as f2:
                f2.write("test content 2")

            # Write a project file
            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.files.add('test2.txt')
            pf.save()

            result = self.runner.invoke(cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE, result)

    def test_brain_create_invalid_project_file(self):
        """ Tests graceful error if `bonsai create` is run where project file
        has invalid content. """
        with temp_filesystem(self):
            self._add_config()

            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.save()

            result = self.runner.invoke(cli, ['create', 'mybrain'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue("Unable to find" in result.output)

    def test_brain_create_invalid_dotbrains(self):
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['create', 'mybrain'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def test_brain_create_file_too_large(self):
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            with open('bigfile.txt', 'wb') as f:
                f.seek(1073741824-1)
                f.write(b"\0")

            pf = ProjectFile()
            pf.files.add('bigfile.txt')
            pf.save()

            result = self.runner.invoke(cli, ['create', 'mybrain'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('exceeds our size limit' in result.output)

    def test_brain_create_with_project_type(self):
        self.api.get_brain_exists = Mock(return_value=False)
        self.api.get_brain_files.return_value = {
            'test.txt': b'# test file 1',
            'test2.txt': b'# test file 2'
        }

        with temp_filesystem(self):
            self._add_config()

            # Create brain using project-type arg.
            args = ['create', 'mybrain']
            args.extend(['--project-type', 'demos/cartpole'])
            result = self.runner.invoke(cli, args)

            # Check create brain network call occurred with expected args.
            self.api.create_brain.assert_called_with(
                "mybrain", project_type="demos/cartpole")
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Check download step occurred.
            saved_files = os.listdir('.')
            self.assertIn('test.txt', saved_files)
            self.assertIn('test2.txt', saved_files)

    def test_brain_create_with_unknown_project_type(self):
        # Mock create brain api call that raises expected error when given
        # unknown project type.
        def _side_effect_create_brain(brain, project_file=None,
                                      project_type=None):
            if project_type and project_type not in (
                    "templates/starter-project",
                    "demos/mountain-car",
                    "demos/cartpole"):
                raise BrainServerError
            else:
                return {}

        self.api.get_brain_exists = Mock(return_value=False)
        self.api.create_brain = Mock(return_value={},
                                     side_effect=_side_effect_create_brain)

        with temp_filesystem(self):
            self._add_config()

            # Create brain using project-type arg
            args = ['create', 'mybrain']
            args.extend(['--project-type', 'unknown'])
            result = self.runner.invoke(cli, args)

            # Check create brain network call occurred with expected args.
            self.api.create_brain.assert_called_with("mybrain",
                                                     project_type="unknown")
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

    def test_brain_create_with_project_type_nonempty_directory(self):
        self.api.get_brain_exists = Mock(return_value=False)

        with temp_filesystem(self):
            self._add_config()

            # Make it nonempty.
            os.mkdir('subfolder')

            # Create brain using project-type arg
            args = ['create', 'mybrain']
            args.extend(['--project-type', 'demos/cartpole'])
            result = self.runner.invoke(cli, args)

            # Check expected message to user.
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue(result.output.startswith(
                "Error: Refusing to create and download"))

    def test_brain_create_invalid_json(self):
        """ Test bonsai create throws error when projfile
            is not in proper json format
        """
        with temp_filesystem(self):
            self._add_config()

            with open('bonsai_brain.bproj', 'w') as f:
                content = '{"files": ["*.ink",],"training":' \
                          '{"simulator": "custom"}}'
                f.write(content)

            result = self.runner.invoke(cli, ['create', 'mybrain'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue(result.output.startswith(
                 "ERROR: Bonsai Create Failed."))

    def _check_payload(self, payload, expected_files_list):
        self.assertTrue("description" in payload, "description field")
        self.assertTrue("project_file" in payload, "project_file field")
        self.assertTrue("name" in payload["project_file"], "name field")
        self.assertTrue("content" in payload["project_file"], "content field")
        self.assertTrue("project_accompanying_files" in payload,
                        "project_accompanying_files field")
        for f in expected_files_list:
            self.assertTrue(f in payload["project_accompanying_files"],
                            "f={} project_accompanying_files field".format(f))

    @patch.object(BonsaiAPI, 'validate', return_value={})
    def test_bonsai_configure(self, validate_mock):
        with temp_filesystem(self):
            # Run `bonsai configure`
            result = self.runner.invoke(
                cli, ['configure'], input=USERNAME + '\n' + ACCESS_KEY)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue(
                'https://beta.bons.ai/accounts/settings/key' in result.output)

            # Check ~/.bonsai
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")

                self.assertTrue("accesskey = {}".format(ACCESS_KEY) in lines)
                self.assertTrue("url = https://api.bons.ai" in lines)
                self.assertTrue("username = {}".format(USERNAME) in lines)

    @patch.object(BonsaiAPI, 'validate', return_value={})
    def test_bonsai_configure_key_option(self, validate_mock):
        with temp_filesystem(self):
            # add a profile to .bonsai
            result = self.runner.invoke(
                cli, ['switch', '--url', 'FOO', 'FIZZ'])
            # Run `bonsai configure --key <some_key>`
            result = self.runner.invoke(
                cli, ['configure', '--access_key', ACCESS_KEY], input=USERNAME)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            # Check ~/.bonsai
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")

                self.assertTrue("accesskey = {}".format(ACCESS_KEY) in lines)
                self.assertTrue("url = FOO" in lines)
                self.assertTrue("username = {}".format(USERNAME) in lines)

    @patch.object(BonsaiAPI, 'validate', return_value={})
    def test_bonsai_configure_username_and_key_option(self, validate_mock):
        with temp_filesystem(self):
            # add a profile to .bonsai
            result = self.runner.invoke(
                cli, ['switch', '--url', 'FOO', 'FIZZ'])
            # Run `bonsai configure --key <some_key>`
            cli_args = [
                'configure',
                '--username',
                USERNAME,
                '--access_key',
                ACCESS_KEY
            ]
            result = self.runner.invoke(cli, cli_args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            # Check ~/.bonsai
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")

                self.assertTrue("accesskey = {}".format(ACCESS_KEY) in lines)
                self.assertTrue("url = FOO" in lines)
                self.assertTrue("username = {}".format(USERNAME) in lines)

    @patch.object(BonsaiAPI, 'validate', return_value={})
    def test_configure_uses_correct_use_color_value(self, validate_mock):
        """
        Tests that the value of use_color is correct when it is changed
        and bonsai configure is run again.
        """
        with temp_filesystem(self):
            # add a profile to .bonsai
            result = self.runner.invoke(
                cli, ['switch', '--url', 'FOO', 'FIZZ'])
            # Run `bonsai configure --key <some_key>`
            cli_args = [
                'configure',
                '--username',
                USERNAME,
                '--access_key',
                ACCESS_KEY
            ]
            result = self.runner.invoke(cli, cli_args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Check ~/.bonsai
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")
                self.assertTrue("accesskey = {}".format(ACCESS_KEY) in lines)
                self.assertTrue("url = FOO" in lines)
                self.assertTrue("username = {}".format(USERNAME) in lines)
                self.assertTrue("use_color = True" in lines)

            # Check that use_color changes to false
            result = self.runner.invoke(cli, ['--disable-color'])
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")
                self.assertTrue("use_color = False" in lines)

            # Check that use_color keeps the same value when reconfiguring
            result = self.runner.invoke(cli, cli_args)
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")
                self.assertTrue("use_color = False" in lines)

    @patch.object(BonsaiAPI, 'validate', return_value={})
    def test_color_options(self, validate_mock):
        """ Tests that `--enable-color/--disable-color` work as intended """
        with temp_filesystem(self):
            # add a profile to .bonsai
            self.runner.invoke(cli, ['switch', '--url', 'FOO', 'FIZZ'])

            # Run `bonsai configure`
            result = self.runner.invoke(
                cli, ['configure'], input=USERNAME + '\n' + ACCESS_KEY)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue(
                'FOO/accounts/settings/key' in result.output)

            # Check ~/.bonsai
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")
                self.assertTrue("accesskey = {}".format(ACCESS_KEY) in lines)
                self.assertTrue("url = FOO" in lines)
                self.assertTrue("username = {}".format(USERNAME) in lines)
                self.assertTrue("use_color = True" in lines)

            result = self.runner.invoke(cli, ['--disable-color'])
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")
                self.assertTrue("use_color = False" in lines)

            result = self.runner.invoke(cli, ['--enable-color'])
            path = os.path.expanduser('~/.bonsai')
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")
                self.assertTrue("use_color = True" in lines)

    @patch.object(BonsaiAPI, 'validate', return_value={})
    def test_bonsai_configure_show_option(self, validate_mock):
        with temp_filesystem(self):
            # add a profile to .bonsai
            result = self.runner.invoke(cli,
                                        ['switch', '--url', 'FOO', 'FIZZ'])
            # Run `bonsai configure --show`
            result = self.runner.invoke(cli, ['configure', '--show'],
                                        input=USERNAME + '\n' + ACCESS_KEY)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue(
                'FOO' in result.output)
            self.assertTrue('Profile Information' in result.output)

    def test_bonsai_switch_new_profile(self):
        with temp_filesystem(self):
            # Create a new profile with --url option
            result = self.runner.invoke(cli,
                                        ['switch', '--url', 'FOO', 'FIZZ'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Attempt to switch to a profile that does not exist
            result = self.runner.invoke(cli, ['switch', 'FOO'])
            self.assertTrue("Profile not found" in result.output)

    def test_bonsai_switch_valid_profile(self):
        with temp_filesystem(self):
            # Create new profile and switch to it
            result = self.runner.invoke(cli, ['switch', '--url', 'BAR', 'FOO'])
            result = self.runner.invoke(cli, ['switch', 'FOO'])
            self.assertTrue("Success!" in result.output)

    def test_bonsai_switch_profile_with_show_option(self):
        with temp_filesystem(self):
            # Create new profile and switch to it
            result = self.runner.invoke(cli, ['switch', '--url', 'BAR', 'FOO'])
            result = self.runner.invoke(cli, ['switch', '--show', 'FOO'])
            self.assertTrue("Success!" in result.output)
            self.assertTrue("Profile Information" in result.output)

    def test_bonsai_switch_prints_available_profiles(self):
        """ Test that `bonsai switch` prints Available Profiles """
        with temp_filesystem(self):
            # Create a new profile named Fizz and check output of cli
            self.runner.invoke(cli, ['switch', 'FIZZ', '--url', 'bar'])
            result = self.runner.invoke(cli, ['switch'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue("Available Profiles:" in result.output)
            self.assertTrue("FIZZ" in result.output)

    def test_bonsai_switch_show_prints_active_profile(self):
        """ Test that `bonsai switch --show` prints Active Profile """
        with temp_filesystem(self):
            self.runner.invoke(cli, ['switch', 'FOO', '--url', 'bar'])
            result = self.runner.invoke(cli, ['switch', '--show'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue("Profile Information" in result.output)

    @patch.object(BonsaiAPI, 'validate', return_value={})
    def test_bonsai_switch_prints_default_profile(self, validate_mock):
        """ Test that `bonsai switch` behaves
            correctly with DEFAULT profile """
        with temp_filesystem(self):
            cli_args = [
                'configure',
                '--username',
                USERNAME,
                '--access_key',
                ACCESS_KEY
            ]
            self.runner.invoke(cli, cli_args)
            self.runner.invoke(cli, ['switch', 'DEFAULT'])
            result = self.runner.invoke(cli, ['switch', '--show'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue("username: " in result.output)

            result = self.runner.invoke(cli, ['switch'])
            self.assertTrue("DEFAULT (active)" in result.output)

    def test_brain_list_with_dotbrains(self):
        brains = [
            {"name": "brain_a", "state": "Stopped"},
            {"name": "brain_b", "state": "Not Started"}
        ]
        self.api.list_brains = Mock(return_value={"brains": brains})

        with temp_filesystem(self):
            db = DotBrains()
            db.add('brain_a')
            db.add('brain_b')
            # Run `bonsai list`
            result = self.runner.invoke(cli, ['list'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Convert table string into list of lists
            # i.e. "brain_b  Not Started" -> ["brain_b", "Not Started"]
            table_string = result.output
            table_lines = table_string.split("\n")
            try:
                brain_lines = [l.split(sep=None, maxsplit=2)
                               for l in table_lines if "brain_" in l]
            except TypeError:
                brain_lines = [l.split(None, 2)
                               for l in table_lines if "brain_" in l]

            # Check values. Note that the default brain is marked
            # NB: DotBrains defines the default brain as the last added
            self.assertEqual(brain_lines[0], ["brain_a", "Stopped"])
            self.assertEqual(brain_lines[1], ["brain_b*", "Not", "Started"])

    def test_brain_list_no_dotbrains(self):
        brains = [
            {"name": "brain_a", "state": "Stopped"},
            {"name": "brain_b", "state": "Not Started"}
        ]
        self.api.list_brains = Mock(return_value={"brains": brains})

        with temp_filesystem(self):
            # Run `bonsai list`
            result = self.runner.invoke(cli, ['list'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Convert table string into list of lists
            # i.e. "brain_b  Not Started" -> ["brain_b", "Not Started"]
            table_string = result.output
            table_lines = table_string.split("\n")
            try:
                brain_lines = [l.split(sep=None, maxsplit=1)
                               for l in table_lines if "brain_" in l]
            except TypeError:
                brain_lines = [l.split(None, 1)
                               for l in table_lines if "brain_" in l]

            # Check values. No default brain is marked
            self.assertEqual(brain_lines[0], ["brain_a", "Stopped"])
            self.assertEqual(brain_lines[1], ["brain_b", "Not Started"])

    def test_brain_list_json_option(self):
        brains = [
            {"name": "brain_a", "state": "Stopped"},
            {"name": "brain_b", "state": "Not Started"}
        ]
        self.api.list_brains = Mock(return_value={"brains": brains})

        with temp_filesystem(self):
            # Run `bonsai list`
            result = self.runner.invoke(cli, ['list', '--json'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            # Throws error if not valid json
            loads(result.output)

    @patch('bonsai_cli.bonsai._check_inkling', return_value=True)
    def test_brain_push(self, patched_inkling_check):
        """ Tests `bonsai push` """
        def _side_effect_edit_brain(brain, project_file):
            # Checks arguments for BonsaiAPI.edit_brain(..) """
            self.assertEqual(brain, "mybrain")
            self.assertTrue(project_file.exists())
            self.assertTrue('test.txt' in project_file.files)
            self.assertTrue('test2.txt' in project_file.files)

            # Checks payload/filesdata that will be sent.
            tempapi = BonsaiAPI(None, None, None)
            (payload, filesdata) = tempapi._payload_edit_brain(project_file)
            self._check_payload(payload, ["test.txt", "test2.txt"])
            self.assertDictEqual(filesdata, {"test.txt": b'test content',
                                             "test2.txt": b'test content 2',
                                             "test3.ink": b'test content 3'})
            self.assertTrue("name" not in payload)

            return {"files": ["bonsai_brain.bproj", "test.txt", "test2.txt"],
                    "ink_compile": "compiler_errors_and_warnings"}
        self.api.edit_brain = Mock(side_effect=_side_effect_edit_brain)
        self.api.get_brain_status = Mock(
            return_value={'state': 'Not Started'})

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            # Write some files.
            with open('test.txt', 'w') as f1:
                f1.write("test content")
            with open('test2.txt', 'w') as f2:
                f2.write("test content 2")
            with open('test3.ink', 'w') as f3:
                f3.write("test content 3")

            # Write a project file
            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.files.add('test2.txt')
            pf.files.add('test3.ink')
            pf.save()

            result = self.runner.invoke(cli, ['push'])
            self.assertTrue("bonsai_brain.bproj" in result.output)
            self.assertTrue("test.txt" in result.output)
            self.assertTrue("test2.txt" in result.output)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE, result)

    @patch('bonsai_cli.bonsai._check_inkling', return_value=True)
    def test_brain_push_json_option(self, patched_inkling_check):
        """ Tests `bonsai push` """
        def _side_effect_edit_brain(brain, project_file):
            # Checks arguments for BonsaiAPI.edit_brain(..) """
            self.assertEqual(brain, "mybrain")
            self.assertTrue(project_file.exists())
            self.assertTrue('test.txt' in project_file.files)
            self.assertTrue('test2.txt' in project_file.files)

            # Checks payload/filesdata that will be sent.
            tempapi = BonsaiAPI(None, None, None)
            (payload, filesdata) = tempapi._payload_edit_brain(project_file)
            self._check_payload(payload, ["test.txt", "test2.txt"])
            self.assertDictEqual(filesdata, {"test.txt": b'test content',
                                             "test2.txt": b'test content 2',
                                             "test3.ink": b'test content 3'})
            self.assertTrue("name" not in payload)

            return {"files": ["bonsai_brain.bproj", "test.txt", "test2.txt"],
                    "ink_compile": "compiler_errors_and_warnings"}
        self.api.edit_brain = Mock(side_effect=_side_effect_edit_brain)
        self.api.get_brain_status = Mock(
            return_value={'state': 'Not Started'})

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            # Write some files.
            with open('test.txt', 'w') as f1:
                f1.write("test content")
            with open('test2.txt', 'w') as f2:
                f2.write("test content 2")
            with open('test3.ink', 'w') as f3:
                f3.write("test content 3")

            # Write a project file
            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.files.add('test2.txt')
            pf.files.add('test3.ink')
            pf.save()

            result = self.runner.invoke(cli, ['push', '--json'])
            self.assertTrue("bonsai_brain.bproj" in result.output)
            self.assertTrue("test.txt" in result.output)
            self.assertTrue("test2.txt" in result.output)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE, result)
            # Throws error if not valid json
            loads(result.output)

    def test_brain_push_during_training(self):
        self.api.get_brain_status = Mock(return_value={'state': 'In Progress'})
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            # Write some files.
            with open('test.txt', 'w') as f1:
                f1.write("test content")
            with open('test2.txt', 'w') as f2:
                f2.write("test content 2")
            with open('test3.ink', 'w') as f3:
                f3.write("test content 3")

            # Write a project file
            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.files.add('test2.txt')
            pf.files.add('test3.ink')
            pf.save()

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

    def test_brain_push_invalid_json_in_projfile(self):
        """ Test bonsai push throws error when projfile
            is not in proper json format
        """
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            with open('bonsai_brain.bproj', 'w') as f:
                content = '{"files": ["*.ink",],"training":' \
                          '{"simulator": "custom"}}'
                f.write(content)

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue(result.output.startswith(
                 "ERROR: Bonsai Push Failed."))

    def test_brain_push_no_project_file(self):
        """ Tests there is graceful error  if `bonsai push` is run in
        directory without a project file.
        """
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue(result.output.startswith(
                "Error: Unable to locate project file"))

    def test_brain_push_invalid_inkling(self):
        """ Tests that inkling errors are printed in bonsai push """
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            # Write some files.
            with open('test.txt', 'w') as f1:
                f1.write("test content")
            with open('test2.txt', 'w') as f2:
                f2.write("test content 2")
            with open('test3.ink', 'w') as f3:
                f3.write("test content 3")
            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.files.add('test2.txt')
            pf.files.add('test3.ink')
            pf.save()

            mock_response = {
                'files': ['test.txt', 'test2.txt', 'test3.ink'],
                'ink_compile': {
                    'errors': [{'code': 'Error.',
                                'column': '1',
                                'line': '2',
                                'text': 'error message'}],
                    'warnings': [{'code': 'Warning. ',
                                  'column': '3',
                                  'line': '4',
                                  'text': 'warning message'}]}
            }
            self.api.edit_brain = Mock(return_value=mock_response)
            self.api.get_brain_status = Mock(
                return_value={'state': 'Not Started'})

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue('Error. ' in result.output)
            self.assertTrue('Warning. ' in result.output)

    def test_brain_push_multiple_inkling(self):
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            # Write some files.
            with open('test.txt', 'w') as f1:
                f1.write("test content")
            with open('test2.ink', 'w') as f2:
                f2.write("test content 2")
            with open('test3.ink', 'w') as f3:
                f3.write("test content 3")
            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.files.add('test2.ink')
            pf.files.add('test3.ink')
            pf.save()

            mock_response = {
                    "description": "",
                    "files": [
                        "cartpole_simulator.py",
                        "requirements.txt",
                        "cartpole.ink",
                        "cartpole2.ink",
                        "bonsai_brain.bproj"
                    ],
                    "ink_compile": {
                        "compiler_version": "1.8.52",
                        "errors": [],
                        "success": "true",
                        "warnings": []
                    },
                    "name": "brain1",
                    "url": "/v1/admin/brain1"
                }
            self.api.edit_brain = Mock(return_value=mock_response)
            self.api.get_brain_status = Mock(
                return_value={'state': 'Not Started'})

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('Multiple inkling ' in result.output)

    def test_brain_push_file_size_too_large(self):
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            with open('bigfile.txt', 'wb') as f:
                f.seek(1073741824-1)
                f.write(b"\0")

            pf = ProjectFile()
            pf.files.add('bigfile.txt')
            pf.save()

            result = self.runner.invoke(cli, ['push'])
            self.assertTrue('exceeds our size limit' in result.output)
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

    def test_brain_push_invalid_dotbrains(self):
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def test_project_option_brain_create(self):
        self.api.get_brain_exists = Mock(return_value=False)
        with temp_filesystem(self):
            self._add_config()
            os.mkdir('subfolder')
            with open('subfolder/test.txt', 'w') as f1:
                f1.write("test content")

            # Create a project in subfolder
            db = DotBrains('subfolder')
            db.add('mybrain')
            pf = ProjectFile.from_file_or_dir('subfolder')
            pf.files.add('test.txt')
            pf.save()

            # Create brain and local file
            result = self.runner.invoke(
                cli, ['create', 'mybrain', '--project', 'subfolder'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

    @patch('bonsai_cli.bonsai._check_inkling', return_value=True)
    def test_project_option_brain_push(self, patched_inkling_check):
        with temp_filesystem(self):
            self._add_config()
            self.api.get_brain_status = Mock(
                return_value={'state': 'Not Started'})
            self.api.edit_brain = Mock(
                return_value={"files": ["bonsai_brain.bproj"],
                              "ink_compile": "compiler_errors_or_warnings"}
            )
            os.mkdir('subfolder')
            with open('subfolder/test.txt', 'w') as f1:
                f1.write("test content")
            with open('subfolder/test2.ink', 'w') as f2:
                f2.write("test content 2")

            # Create a project in subfolder
            db = DotBrains('subfolder')
            db.add('mybrain')
            pf = ProjectFile.from_file_or_dir('subfolder')
            pf.files.add('test.txt')
            pf.files.add('test2.ink')
            pf.save()

            result = self.runner.invoke(
                cli, ['push', '--project', 'subfolder'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

    def test_brain_push_invalid_project_file(self):
        """ Tests graceful error if `bonsai push` is run where project file
        has invalid content. """
        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.save()

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue("Unable to find" in result.output)

    def test_train_start(self):
        """ Tests `bonsai train start`"""
        self.api.get_brain_status = Mock(return_value={'state': 'Not Started'})
        self.api.start_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'start']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.start_training_brain.assert_called_with("mybrain", True)

    def test_train_start_remote(self):
        """ Tests remote flag: `bonsai train start --remote`"""
        self.api.get_brain_status = Mock(return_value={'state': 'Not Started'})
        self.api.start_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'start', '--remote']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.start_training_brain.assert_called_with("mybrain", False)

    def test_train_start_invalid_dotbrains(self):
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['train', 'start'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def test_train_start_json_option(self):
        """ Tests `bonsai train start --json`"""
        self.api.get_brain_status = Mock(return_value={'state': 'Not Started'})
        self.api.start_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'start', '--json']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.start_training_brain.assert_called_with("mybrain", True)
            # Throws error if not valid json
            loads(result.output)

    def test_train_stop_json_option(self):
        """ Tests `bonsai train stop --json`"""
        self.api.get_brain_status = Mock(return_value={'state': 'Not Started'})
        self.api.stop_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'stop', '--json']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.stop_training_brain.assert_called_with("mybrain")
            # Throws error if not valid json
            loads(result.output)

    def test_train_stop_brain_in_error_state(self):
        """ Tests behavior when trying to train a brain in an error state """
        self.api.get_brain_status = Mock(return_value={'state': 'Error'})

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            result = self.runner.invoke(cli, ['train', 'start'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('contact Bonsai Support' in result.output)

    def test_train_resume(self):
        """ Tests `bonsai train resume` """
        self.api.resume_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'resume']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.resume_training_brain.assert_called_with("mybrain",
                                                              "latest", True)

    def test_train_resume_json_option(self):
        """ Tests `bonsai train resume --json` """
        self.api.resume_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'resume', '--json']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.resume_training_brain.assert_called_with("mybrain",
                                                              "latest", True)
            # Throws error if not valid json
            loads(result.output)

    def test_train_resume_remote(self):
        """ Tests `bonsai train resume --remote` """
        self.api.resume_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'resume', '--remote']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.resume_training_brain.assert_called_with("mybrain",
                                                              "latest", False)

    def test_train_resume_invalid_dotbrains(self):
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['train', 'resume'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def test_train_status_json_option(self):
        """ Tests `bonsai train status --json` """
        self.api.get_brain_status = Mock(return_value={
            'status': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'status', '--json']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            # Throws error if not valid json
            loads(result.output)

    def test_sims_list_json_option(self):
        """ Tests `bonsai sims list --json` """
        self.api.get_brain_status = Mock(return_value={
            'simulators': ''
        })

        with temp_filesystem(self):
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'status', '--json']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            # Throws error if not valid json
            loads(result.output)

    def test_brain_create_sets_default(self):
        self.api.get_brain_exists = Mock(return_value=False)
        with temp_filesystem(self):
            self._add_config()

            db = DotBrains()
            db.add('mybrain')
            db.add('other')
            current = db.get_default()
            self.assertEqual(current.name, 'other')

            result = self.runner.invoke(
                cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            db = DotBrains()
            current = db.get_default()
            self.assertEqual(current.name, 'mybrain')

    def _brain_option(self, args, mock, extra_args=None):
        """ Common code for testing the brain parameter flag """
        extra_args = extra_args or []

        mock.return_value = {}
        with temp_filesystem(self):
            self._add_config()

            # No Brain specified
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

            # with .brains
            db = DotBrains()
            db.add('default_brain')
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            expected_args = ['default_brain'] + extra_args
            mock.assert_called_with(*expected_args)

            # with parameter
            args.extend(['--brain', 'mybrain'])
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            expected_args = ['mybrain'] + extra_args
            mock.assert_called_with(*expected_args)

    def test_brain_option_sims_list(self):
        self._brain_option(['sims', 'list'], self.api.list_simulators)

    def test_brain_option_train_start(self):
        # Expected arguments to api.start_training_brain()
        self.api.get_brain_status = Mock(return_value={'state': 'Not Started'})
        extra_args = [True]
        self._brain_option(
            ['train', 'start'], self.api.start_training_brain, extra_args
        )

    def test_brain_option_train_stop(self):
        self._brain_option(['train', 'stop'], self.api.stop_training_brain)

    def test_brain_option_train_status(self):
        self._brain_option(['train', 'status'], self.api.get_brain_status)

    def test_train_status_invalid_dotbrains(self):
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['train', 'status'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def test_train_stop_invalid_dotbrains(self):
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['train', 'stop'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def test_sims_list_invalid_dotbrains(self):
        with temp_filesystem(self):
            self._add_config()
            invalid_brains = "{'brains': [{'brain'}}"
            with open('.brains', 'w') as f1:
                f1.write(invalid_brains)

            result = self.runner.invoke(cli, ['sims', 'list'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue('ERROR: Bonsai Command Failed' in result.output)

    def _project_option(self, args, mock, extra_args=None):
        """ Common code for testing the project parameter flag """
        extra_args = extra_args or []

        mock.return_value = {}
        with temp_filesystem(self):
            self._add_config()
            os.mkdir('subfolder')
            db = DotBrains('subfolder')
            db.add('subfolder_brain')

            args.extend(['--project', 'subfolder'])
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            expected_args = ['subfolder_brain'] + extra_args
            mock.assert_called_with(*expected_args)

    def test_project_option_train_status(self):
        self._project_option(['train', 'status'], self.api.get_brain_status)

    def test_project_option_train_start(self):
        # Expected arguments to api.start_training_brain()
        self.api.get_brain_status = Mock(return_value={'state': 'Not Started'})
        extra_args = [True]
        self._project_option(
            ['train', 'start'], self.api.start_training_brain, extra_args
        )

    def test_project_option_train_stop(self):
        self._project_option(['train', 'stop'], self.api.stop_training_brain)

    def test_project_option_sims_list(self):
        self._project_option(['sims', 'list'], self.api.list_simulators)

    def test_project_option_with_brain(self):
        """ Project directory and brain both specified """
        mock = self.api.get_brain_status
        mock.return_value = {}
        with temp_filesystem(self):
            self._add_config()
            os.mkdir('subfolder')
            db = DotBrains('subfolder')
            db.add('subfolder_brain')

            args = ['train', 'status']
            args.extend(['--project', 'subfolder'])
            args.extend(['--brain', 'somebrain'])
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            mock.assert_called_with('somebrain')

    def test_project_option_missing_dotbrains(self):
        """ Project directory has no .brains file """
        with temp_filesystem(self):
            self._add_config()
            os.mkdir('subfolder')

            args = ['train', 'status']
            args.extend(['--project', 'subfolder'])
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

    def test_project_option_missing_directory(self):
        """ Project directory does not exist """
        with temp_filesystem(self):
            self._add_config()

            args = ['train', 'status']
            args.extend(['--project', 'new_bogus_folder'])
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

    def test_timeout_option(self):
        with temp_filesystem(self):
            result = self.runner.invoke(cli, ['--timeout', 10, 'list'])
            assert BonsaiAPI.TIMEOUT == 10
            result = self.runner.invoke(cli, ['--timeout', 35, 'list'])
            assert BonsaiAPI.TIMEOUT == 35


class TestPyPiVersionRequest(TestCase):
    """ Contains all the tests for --version in cli """
    def setUp(self):
        self.runner = CliRunner()

        self.req_fail_output = 'Bonsai ' + __version__ + '\n' \
                               'Unable to connect to PyPi and ' \
                               'determine if CLI is up to date.\n'
        self.not_up_to_date_output = 'Bonsai ' + __version__ + '\nBonsai ' \
                                     'update available. The most recent ' \
                                     'version is : 9999\nUpgrade via pip ' \
                                     'using \'pip install --upgrade ' \
                                     'bonsai-cli\'\n'
        self.up_to_date_output = 'Bonsai ' + __version__ + \
                                 '\nEverything is up to date.\n'

    def test_get_pypi_version_valid_url(self):
        """ Test PyPi version request with valid url """
        _get_pypi_version = Mock(return_value='0.8.14')
        pypi_version = _get_pypi_version('valid_url')
        self.assertNotEqual(pypi_version, None)

    def test_get_pypi_version_invalid_url(self):
        """ Test PyPi version request with invalid url """
        _get_pypi_version = Mock(return_value=None)
        pypi_version = _get_pypi_version('invalid_url')
        self.assertEqual(pypi_version, None)

    @patch('bonsai_cli.bonsai._get_pypi_version', return_value=None)
    def test_request_fail_cli_output(self, patched_function):
        """ Test output when request failure/json failure """
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
        self.assertEqual(result.output, self.req_fail_output)

    @patch('bonsai_cli.bonsai._get_pypi_version', return_value='9999')
    def test_version_not_up_to_date_cli_output(self, patched_function):
        """ Test output when cli is out of date """
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
        self.assertEqual(result.output, self.not_up_to_date_output)

    @patch('bonsai_cli.bonsai._get_pypi_version', return_value=__version__)
    def test_version_up_to_date_cli_output(self, patched_function):
        """ Test output when cli is up to date """
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
        self.assertEqual(result.output, self.up_to_date_output)


class TestSysInfo(TestCase):
    """ Test cases for --sysinfo (top level option)"""
    BONSAI_BACKUP = './bonsai.bak'

    def setUp(self):
        self.runner = CliRunner()

    def test_sysinfo(self):
        result = self.runner.invoke(cli, ['--sysinfo'])
        self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
        self.assertIn("Platform", result.output)
        self.assertIn("Package", result.output)
        self.assertIn("Profile", result.output)

    def test_no_dotbonsai(self):
        with temp_filesystem(self):
            result = self.runner.invoke(cli, ['--sysinfo'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # assert that there is no profile info to print
            self.assertEqual("-\n", result.output[-2:])
