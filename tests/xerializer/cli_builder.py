# from torch_train_manager import cli_builder as mdl
from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
import subprocess as subp
import yaml


class TestFunctions(TestCase):

    def test_all(self):
        with TemporaryDirectory() as temp_dir:

            temp_dir = Path(temp_dir)
            root = Path(__file__).parent / '_cli_builder_helpers'

            # Check that output file does not exist.
            with open(root / 'config.yaml') as fo:
                created_file = temp_dir / yaml.safe_load(fo.read())['filename']
            self.assertFalse(created_file.is_file())

            completed = subp.run(
                ['python',
                 root / 'cli.py',
                 root / 'config.yaml',
                 temp_dir])
            completed.check_returncode()

            # Check that output file exists.
            self.assertTrue(created_file.is_file())
