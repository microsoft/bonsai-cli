"""
This file contains unit tests for bonsai command line.
"""
from unittest import TestCase

from click.testing import CliRunner

from bonsai_cli.bonsai import cli


SUCCESS_EXIT_CODE = 0
FAILURE_EXIT_CODE = 1


class TestBrainCommand(TestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_brain_load_ink_file_not_found(self):
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(
                cli, ['brain', 'load', 'mybrain', 'notfound.ink'])

        # This test will currently fail, either because the current
        # machine isn't configured (and the access key won't be found)
        # or because the file notfound.ink won't be found.
        # TODO: Fix this so that failure due to missing access key
        # is a separate test.
        self.assertEqual(result.exit_code, FAILURE_EXIT_CODE)
