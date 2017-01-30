"""
This file contains unit tests for dotbrains.py
"""
from unittest import TestCase
from bonsai_cli.dotbrains import DotBrains

from click.testing import CliRunner


class TestDotBrains(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_dotbrains_does_not_exist(self):
        with self.runner.isolated_filesystem():
            db = DotBrains()
            self.assertEqual(0, len(db.brains))

    def test_add_brain(self):
        with self.runner.isolated_filesystem():
            db = DotBrains()
            db.add('brain1')
            self.assertEqual(1, len(db.brains))

            # added brain is the default
            self.assertTrue(db.brains[0].default)

            # brain also exists on re-load
            db2 = DotBrains()
            self.assertEqual(1, len(db2.brains))
            b1 = db2.find('brain1')
            self.assertEqual('brain1', b1.name)

    def test_change_default(self):
        with self.runner.isolated_filesystem():
            db = DotBrains()
            db.add('brain1')
            db.add('brain2')

            b2 = db.find('brain2')
            self.assertTrue(b2.default)

            b1 = db.find('brain1')
            self.assertFalse(b1.default)

            db.set_default(b1)
            self.assertTrue(b1.default)

    def test_get_default(self):
        with self.runner.isolated_filesystem():
            db = DotBrains()
            db.add('brain1')
            db.add('brain2')

            brain = db.get_default()
            self.assertEqual(brain.name, 'brain2')
