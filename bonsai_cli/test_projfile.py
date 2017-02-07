"""
This file contains unit tests for projfile.py
"""
import os
from unittest import TestCase
from bonsai_cli.projfile import ProjectFile, ProjectFileInvalidError

from click.testing import CliRunner


class TestProjectFile(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_single_inkling(self):
        with self.runner.isolated_filesystem():
            open('one.ink', 'a').close()
            pf = ProjectFile()
            pf.files.add('./')

            self.assertTrue(pf.inkling_file.endswith('./one.ink'))

    def test_inkling_specified(self):
        with self.runner.isolated_filesystem():
            open('one.ink', 'a').close()
            open('two.ink', 'a').close()
            pf = ProjectFile()
            pf.files.add('./')
            pf.inkling_file = 'two.ink'
            self.assertEqual(pf.inkling_file, 'two.ink')

    def test_missing_inkling(self):
        with self.runner.isolated_filesystem():
            pf = ProjectFile()
            with self.assertRaises(ProjectFileInvalidError):
                pf.inkling_file

    def test_inkling_conflict(self):
        with self.runner.isolated_filesystem():
            open('one.ink', 'a').close()
            open('two.ink', 'a').close()
            pf = ProjectFile()
            pf.files.add('./')
            with self.assertRaises(ProjectFileInvalidError):
                pf.inkling_file

    def test_inkling_subdir(self):
        with self.runner.isolated_filesystem():
            os.mkdir('sub')
            os.mkdir('sub/sub2')
            open('sub/sub2/one.ink', 'a').close()
            pf = ProjectFile()
            pf.files.add('./')
            self.assertTrue(pf.inkling_file.endswith('./sub/sub2/one.ink'))
            self.assertTrue(os.path.isfile(pf.inkling_file))

    def test_outside_dir(self):
        with self.runner.isolated_filesystem():
            os.mkdir('sub')
            os.mkdir('sub/sub2')
            os.mkdir('sub/sub3')
            pf = ProjectFile('sub/sub3/test.bproj')
            pf.files.add('./')
            pf.files.add('something.ink')
            pf.files.add('../sub2/somethingelse.ink')
            pf.files.add('/tmp/athirdthing.ink')

            all_paths = list(pf._list_paths())
            self.assertEqual(1, len(all_paths))
            self.assertIn('something.ink', all_paths)
