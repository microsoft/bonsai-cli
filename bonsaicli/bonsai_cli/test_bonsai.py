"""
This file contains unit tests for bonsai command line.
"""
import os
from unittest import TestCase
from unittest.mock import Mock, patch

from click.testing import CliRunner

from bonsai_cli.api import BrainServerError
from bonsai_cli.bonsai import cli
from bonsai_cli.dotbrains import DotBrains
from bonsai_config import BonsaiConfig

SUCCESS_EXIT_CODE = 0
FAILURE_EXIT_CODE = 1


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

    def test_brain_load_ink_file_not_found(self):
        with self.runner.isolated_filesystem():
            self._add_config()

            result = self.runner.invoke(
                cli, ['load', '--brain', 'mybrain', 'notfound.ink'])

        self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)

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

    def _brain_option(self, args, mock):
        """ Common code for testing the brain parameter flag """
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
            mock.assert_called_with('default_brain')

            # with parameter
            args.extend(['--brain', 'mybrain'])
            result = self.runner.invoke(cli, args)
            self.assertEqual(result.exit_code, SUCCESS_EXIT_CODE)
            mock.assert_called_with('mybrain')

    def test_sims_list(self):
        self._brain_option(['sims', 'list'], self.api.list_simulators)

    def test_train_start(self):
        self._brain_option(['train', 'start'], self.api.start_training_brain)

    def test_train_stop(self):
        self._brain_option(['train', 'stop'], self.api.stop_training_brain)

    def test_train_status(self):
        self._brain_option(['train', 'status'], self.api.get_brain_status)
