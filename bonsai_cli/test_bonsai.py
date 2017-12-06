"""
This file contains unit tests for bonsai command line.
"""
import os
from unittest import TestCase

# python 3.3+ includes mock in the unittest module
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from click.testing import CliRunner

from bonsai_cli import __version__
from bonsai_cli.api import BrainServerError, BonsaiAPI
from bonsai_cli.bonsai import cli, _get_pypi_version
from bonsai_cli.dotbrains import DotBrains
from bonsai_cli.projfile import ProjectFile
from bonsai_config import BonsaiConfig

SUCCESS_EXIT_CODE = 0
FAILURE_EXIT_CODE = 1
ACCESS_KEY = '00000000-1111-2222-3333-000000000001'
USERNAME = 'admin'


def _print_result(result):
    """Debugging method to print the output returned from click."""
    print(result.output)
    print(result.exception)
    import traceback
    traceback.print_tb(result.exc_info[2])


class TestBrainCommand(TestCase):

    def setUp(self):
        self._clean_dotbonsai()
        self.runner = CliRunner()

    def _clean_dotbonsai(self):
        path = os.path.expanduser('~/.bonsai')
        if os.path.isfile(path):
            os.remove(path)

    def test_missing_access_key(self):
        result = self.runner.invoke(cli, ['list'])

        self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

    def test_missing_parameter_create(self):
        result = self.runner.invoke(cli, ['create'])

        self.assertNotEqual(result.exit_code, SUCCESS_EXIT_CODE)

    def test_missing_parameter_delete(self):
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

        config = BonsaiConfig()
        config.update_access_key_and_username(ACCESS_KEY, USERNAME)

    def test_brain_download(self):
        self.api.get_brain_files.return_value = {
            'test.txt': b'# test file 1',
            'test2.txt': b'# test file 2'
        }

        with self.runner.isolated_filesystem():
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

    def test_brain_delete(self):
        with self.runner.isolated_filesystem():
            self._add_config()

            # Brain exists, delete succeeds
            brain_set = {'brains': [{'name': 'mybrain'}]}
            self.api.list_brains = Mock(return_value=brain_set)
            result = self.runner.invoke(
                cli, ['delete', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue("WARNING" in result.output)
            self.assertTrue("deleted" in result.output)

            # Brain does not exist, command completes but prints a
            # message informing user that no action was taken.
            brain_set = {'brains': []}
            self.api.list_brains = Mock(return_value=brain_set)
            result = self.runner.invoke(
                cli, ['delete', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.assertTrue("WARNING" not in result.output)
            self.assertTrue("does not exist. No action" in result.output)

    def test_brain_create(self):
        self.api.list_brains = Mock(return_value={'brains': []})
        with self.runner.isolated_filesystem():
            self._add_config()

            # Create brain and local file
            result = self.runner.invoke(
                cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Both already exist
            open('test.ink', 'a').close()
            open('test_simulator.py', 'a').close()
            brain_set = {'brains': [{'name': 'mybrain'}]}
            self.api.list_brains = Mock(return_value=brain_set)
            result = self.runner.invoke(
                cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Create only local file
            os.remove('.brains')
            result = self.runner.invoke(
                cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Create only remote brain
            self.api.list_brains = Mock(return_value={'brains': []})
            db = DotBrains()
            db.add('mybrain2')
            result = self.runner.invoke(
                cli, ['create', 'mybrain2'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

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
        self.api.list_brains = Mock(return_value={'brains': []})
        self.api.create_brain = Mock(side_effect=_side_effect_create_brain)

        with self.runner.isolated_filesystem():
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
        with self.runner.isolated_filesystem():
            self._add_config()

            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.save()

            result = self.runner.invoke(cli, ['create', 'mybrain'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue("Unable to find" in result.output)

    def test_brain_create_with_project_type(self):
        self.api.list_brains = Mock(return_value={'brains': []})
        self.api.get_brain_files.return_value = {
            'test.txt': b'# test file 1',
            'test2.txt': b'# test file 2'
        }

        with self.runner.isolated_filesystem():
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

        self.api.list_brains = Mock(return_value={'brains': []})
        self.api.create_brain = Mock(return_value={},
                                     side_effect=_side_effect_create_brain)

        with self.runner.isolated_filesystem():
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
        self.api.list_brains = Mock(return_value={'brains': []})

        with self.runner.isolated_filesystem():
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

    @patch.object(BonsaiAPI, 'validate', return_value={'username': USERNAME})
    def test_bonsai_configure(self, validate_mock):
        with self.runner.isolated_filesystem():
            path = os.path.expanduser('~/.bonsai')
            if os.path.isfile(path):
                os.remove(path)

            # Run `bonsai configure`
            result = self.runner.invoke(cli, ['configure'], input=ACCESS_KEY)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Check ~/.bonsai
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")

                self.assertTrue("accesskey = {}".format(ACCESS_KEY) in lines)
                self.assertTrue("url = https://api.bons.ai" in lines)
                self.assertTrue("username = {}".format(USERNAME) in lines)

    @patch.object(BonsaiAPI, 'validate', return_value={'username': USERNAME})
    def test_bonsai_configure_key_option(self, validate_mock):
        with self.runner.isolated_filesystem():
            path = os.path.expanduser('~/.bonsai')
            if os.path.isfile(path):
                os.remove(path)

            # Run `bonsai configure --key <some_key>`
            result = self.runner.invoke(cli,
                                        ['configure', '--key', ACCESS_KEY])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Check ~/.bonsai
            with open(path, 'r') as f:
                result = f.read()
                lines = result.split("\n")

                self.assertTrue("accesskey = {}".format(ACCESS_KEY) in lines)
                self.assertTrue("url = https://api.bons.ai" in lines)
                self.assertTrue("username = {}".format(USERNAME) in lines)

    @patch.object(BonsaiConfig, 'check_section_exists',
                  create=True, return_value=False)
    def test_bonsai_switch_new_profile(self, check_section_mock):
        with self.runner.isolated_filesystem():
            path = os.path.expanduser('~/.bonsai')
            if os.path.isfile(path):
                os.remove(path)

            # Create a new profile with --url option
            result = self.runner.invoke(cli,
                                        ['switch', '--url', 'FOO', 'FIZZ'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Attempt to switch to a profile that does not exist
            result = self.runner.invoke(cli, ['switch', 'FOO'])
            self.assertTrue("Profile not found" in result.output)

    @patch.object(BonsaiConfig, 'check_section_exists',
                  create=True, return_value=True)
    def test_bonsai_switch_valid_profile(self, check_section_mock):
        with self.runner.isolated_filesystem():
            path = os.path.expanduser('~/.bonsai')
            if os.path.isfile(path):
                os.remove(path)

            # Create new profile and switch to it
            result = self.runner.invoke(cli, ['switch', '--url', 'BAR', 'FOO'])
            result = self.runner.invoke(cli, ['switch', 'FOO'])
            self.assertTrue("Success!" in result.output)

    def test_brain_list_with_dotbrains(self):
        brains = [
            {"name": "brain_a", "state": "Stopped"},
            {"name": "brain_b", "state": "Not Started"}
        ]
        self.api.list_brains = Mock(return_value={"brains": brains})

        with self.runner.isolated_filesystem():
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
            self.assertEqual(brain_lines[1], ["->", "brain_b", "Not Started"])

    def test_brain_list_no_dotbrains(self):
        brains = [
            {"name": "brain_a", "state": "Stopped"},
            {"name": "brain_b", "state": "Not Started"}
        ]
        self.api.list_brains = Mock(return_value={"brains": brains})

        with self.runner.isolated_filesystem():
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

    def test_brain_push(self):
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
                                             "test2.txt": b'test content 2'})
            self.assertTrue("name" not in payload)

            return {"files": ["bonsai_brain.bproj", "test.txt", "test2.txt"]}
        self.api.edit_brain = Mock(side_effect=_side_effect_edit_brain)

        with self.runner.isolated_filesystem():
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

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE, result)

    def test_brain_push_no_project_file(self):
        """ Tests there is graceful error  if `bonsai push` is run in
        directory without a project file.
        """
        with self.runner.isolated_filesystem():
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue(result.output.startswith(
                "Error: Unable to locate project file"))

    def test_project_option_brain_create(self):
        self.api.list_brains = Mock(return_value={'brains': []})
        with self.runner.isolated_filesystem():
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

    def test_project_option_brain_push(self):
        with self.runner.isolated_filesystem():
            self._add_config()
            self.api.edit_brain = Mock(
                return_value={"files": [
                    "bonsai_brain.bproj"
                ]})
            os.mkdir('subfolder')
            with open('subfolder/test.txt', 'w') as f1:
                f1.write("test content")

            # Create a project in subfolder
            db = DotBrains('subfolder')
            db.add('mybrain')
            pf = ProjectFile.from_file_or_dir('subfolder')
            pf.files.add('test.txt')
            pf.save()

            result = self.runner.invoke(
                cli, ['push', '--project', 'subfolder'])
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

    def test_brain_push_invalid_project_file(self):
        """ Tests graceful error if `bonsai push` is run where project file
        has invalid content. """
        with self.runner.isolated_filesystem():
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            pf = ProjectFile()
            pf.files.add('test.txt')
            pf.save()

            result = self.runner.invoke(cli, ['push'])
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
            self.assertTrue("Unable to find" in result.output)

    def test_sims_log(self):
        """ Tests `bonsai log` . """
        self.api.get_simulator_logs = Mock(return_value=['line1', 'line2'])

        with self.runner.isolated_filesystem():
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            result = self.runner.invoke(cli, ['log'])
            self.api.get_simulator_logs.assert_called_with(
                "mybrain", "latest", "1")
            self.assertEqual(result.output,
                             'Simulator logs for mybrain:\nline1\nline2\n',
                             result.output)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE, result)

    def test_train_start(self):
        """ Tests `bonsai train start`"""
        self.api.start_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with self.runner.isolated_filesystem():
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'start']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.start_training_brain.assert_called_with("mybrain", True)

    def test_train_start_remote(self):
        """ Tests remote flag: `bonsai train start --remote`"""
        self.api.start_training_brain = Mock(return_value={
            'simulator_predictions_url': ''
        })

        with self.runner.isolated_filesystem():
            self._add_config()
            db = DotBrains()
            db.add('mybrain')

            args = ['train', 'start', '--remote']
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            self.api.start_training_brain.assert_called_with("mybrain", False)

    def test_brain_create_sets_default(self):
        self.api.list_brains = Mock(return_value={'brains': []})
        with self.runner.isolated_filesystem():
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
        with self.runner.isolated_filesystem():
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

    def test_brain_option_sims_log(self):
        # Expected arguments to api.get_simulator_logs()
        extra_args = ["latest", "1"]
        self._brain_option(['log'], self.api.get_simulator_logs, extra_args)

    def test_brain_option_train_start(self):
        # Expected arguments to api.start_training_brain()
        extra_args = [True]
        self._brain_option(
            ['train', 'start'], self.api.start_training_brain, extra_args
        )

    def test_brain_option_train_stop(self):
        self._brain_option(['train', 'stop'], self.api.stop_training_brain)

    def test_brain_option_train_status(self):
        self._brain_option(['train', 'status'], self.api.get_brain_status)

    def _project_option(self, args, mock, extra_args=None):
        """ Common code for testing the project parameter flag """
        extra_args = extra_args or []

        mock.return_value = {}
        with self.runner.isolated_filesystem():
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
        extra_args = [True]
        self._project_option(
            ['train', 'start'], self.api.start_training_brain, extra_args
        )

    def test_project_option_train_stop(self):
        self._project_option(['train', 'stop'], self.api.stop_training_brain)

    def test_project_option_sims_list(self):
        self._project_option(['sims', 'list'], self.api.list_simulators)

    def test_project_option_sims_log(self):
        # Expected arguments to api.get_simulator_logs()
        extra_args = ["latest", "1"]
        self._project_option(['log'], self.api.get_simulator_logs, extra_args)

    def test_project_option_with_brain(self):
        """ Project directory and brain both specified """
        mock = self.api.get_brain_status
        mock.return_value = {}
        with self.runner.isolated_filesystem():
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
        with self.runner.isolated_filesystem():
            self._add_config()
            os.mkdir('subfolder')

            args = ['train', 'status']
            args.extend(['--project', 'subfolder'])
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

    def test_project_option_missing_directory(self):
        """ Project directory does not exist """
        with self.runner.isolated_filesystem():
            self._add_config()

            args = ['train', 'status']
            args.extend(['--project', 'new_bogus_folder'])
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)


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
