from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import seed_clearml


class SeedClearmlTest(unittest.TestCase):
    def test_credentials_are_optional(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(seed_clearml.get_credentials())

    def test_credentials_are_read_from_environment(self):
        environment = {
            "CLEARML_API_ACCESS_KEY": "access-key",
            "CLEARML_API_SECRET_KEY": "secret-key",
        }

        with patch.dict("os.environ", environment, clear=True):
            self.assertEqual(
                seed_clearml.get_credentials(),
                ("access-key", "secret-key"),
            )

    def test_incomplete_credentials_are_rejected(self):
        environment = {"CLEARML_API_ACCESS_KEY": "access-key"}

        with patch.dict("os.environ", environment, clear=True):
            with self.assertRaisesRegex(RuntimeError, "must be set together"):
                seed_clearml.get_credentials()

    @patch("seed_clearml.call")
    def test_existing_project_is_reused(self, call_mock):
        call_mock.return_value = {
            "data": {"projects": [{"id": "project-1", "name": "stackup/test"}]}
        }

        self.assertEqual(seed_clearml.ensure_project(), "project-1")
        call_mock.assert_called_once_with(
            "projects.get_all",
            {"name": "stackup/test", "only_fields": ["id", "name"]},
        )

    @patch("seed_clearml.call")
    def test_missing_task_is_created(self, call_mock):
        call_mock.side_effect = [
            {"data": {"tasks": []}},
            {"data": {"id": "task-1"}},
        ]

        self.assertEqual(seed_clearml.ensure_task("project-1"), "task-1")
        create_endpoint, create_payload = call_mock.call_args_list[1].args
        self.assertEqual(create_endpoint, "tasks.create")
        self.assertEqual(create_payload["project"], "project-1")
        self.assertEqual(create_payload["type"], "testing")


if __name__ == "__main__":
    unittest.main()
