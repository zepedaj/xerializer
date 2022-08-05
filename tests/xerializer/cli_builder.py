# from torch_train_manager import cli_builder as mdl
import json
from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
import subprocess as subp
import yaml


class TestFunctions(TestCase):
    def test_all(self):
        with TemporaryDirectory() as temp_dir:

            temp_dir = Path(temp_dir)
            root = Path(__file__).parent / "_cli_builder_helpers"

            # Check that output file does not exist.
            with open(root / "config.yaml") as fo:
                created_file = temp_dir / yaml.safe_load(fo.read())["filename"]
            self.assertFalse(created_file.is_file())

            subp.check_output(
                [
                    "python",
                    root / "cli.py",
                    root / "config.yaml",
                    temp_dir,
                    text1 := "abc",  # text1 is a positional argument
                    "--text2",
                    text2 := "def",
                ],
                stderr=subp.STDOUT,
            )

            # Check that output file exists.
            self.assertTrue(created_file.is_file())

            # Check contents of output file.
            with open(created_file) as fo:
                contents = json.load(fo)
                self.assertEqual(contents, {"text1": text1, "text2": text2})
