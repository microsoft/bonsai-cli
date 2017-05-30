"""
This file contains unit tests for bonsai command line.
"""
import os
from unittest import TestCase
from unittest.mock import Mock, patch

from click.testing import CliRunner

from bonsai_cli.api import BrainServerError, BonsaiAPI
from bonsai_cli.bonsai import cli
from bonsai_cli.dotbrains import DotBrains
from bonsai_cli.projfile import ProjectFile
from bonsai_config import BonsaiConfig

SUCCESS_EXIT_CODE = 0
FAILURE_EXIT_CODE = 1


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

    def test_missing_parameter(self):
        result = self.runner.invoke(cli, ['create'])

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
            'test.txt': '# test file 1',
            'test2.txt': '# test file 2'
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

    def test_brain_create(self):
        self.api.list_brains = Mock(return_value={'brains': []})
        with self.runner.isolated_filesystem():
            self._add_config()

            # Create brain and local file
            result = self.runner.invoke(
                cli, ['create', 'mybrain'])

            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)

            # Both already exist
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
            'test.txt': '# test file 1',
            'test2.txt': '# test file 2'
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
            self.assertEqual(result.output, 'line1\nline2\n', result.output)
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
