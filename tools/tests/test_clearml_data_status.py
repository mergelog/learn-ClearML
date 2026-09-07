from __future__ import annotations

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock

from tools.clearml_data_status.gateway import collect_status
from tools.clearml_data_status.report import render_status
from tools.semiconductor_seed.config import PROJECT_ROOT


class ClearmlDataStatusTest(unittest.TestCase):
    def test_empty_learning_data_is_reported_separately_from_server_totals(self) -> None:
        client = _client(
            projects=[_record(id="example", name="ClearML Examples")],
            tasks=[_record(id="example-task", project="example")],
            models=[_record(id="example-model", project="example")],
        )

        report = render_status(collect_status(client, "http://localhost:8008"))

        self.assertIn("Project: 1件", report)
        self.assertIn("現在のDatasetデータはありません。", report)
        self.assertIn("現在のTraining Taskデータはありません。", report)
        self.assertIn("半導体学習データはありません。学習開始前の状態です。", report)

    def test_registered_learning_data_includes_counts_and_created_dates(self) -> None:
        created = datetime(2026, 9, 6, 1, 2, 3, tzinfo=timezone.utc)
        project_id = "semiconductor-project"
        client = _client(
            projects=[
                _record(
                    id=project_id,
                    name=PROJECT_ROOT,
                    created=created,
                )
            ],
            tasks=[
                _record(
                    id="dataset-1",
                    project=project_id,
                    name="semiconductor-quality-data",
                    created=created,
                    system_tags=["dataset"],
                    runtime={"version": "1.0.0"},
                    status="completed",
                    type="data_processing",
                ),
                _record(
                    id="training-1",
                    project=project_id,
                    name="random-forest-quality-classifier",
                    created=created,
                    system_tags=[],
                    status="completed",
                    type="training",
                ),
            ],
            models=[
                _record(
                    id="model-1",
                    project=project_id,
                    name="semiconductor-quality-classifier",
                    created=created,
                    framework="scikitlearn",
                )
            ],
        )

        report = render_status(collect_status(client, "http://localhost:8008"))

        self.assertIn("現在のDatasetデータは1件あります。", report)
        self.assertIn("version: 1.0.0", report)
        self.assertIn("現在のTraining Taskデータは1件あります。", report)
        self.assertIn("現在のModelデータは1件あります。", report)
        self.assertIn(
            "作成日時 (Asia/Tokyo): 2026-09-06T10:02:03+09:00",
            report,
        )
        self.assertIn("半導体学習データが登録されています。", report)

    def test_dataset_in_hidden_infrastructure_project_is_reported(self) -> None:
        created = datetime(2026, 9, 6, 1, 2, 3, tzinfo=timezone.utc)
        root_project_id = "semiconductor-project"
        dataset_project_id = "hidden-dataset-project"
        dataset_project_name = (
            f"{PROJECT_ROOT}/.datasets/semiconductor-quality-data"
        )
        client = _client(
            projects=[
                _record(id=root_project_id, name=PROJECT_ROOT, created=created),
            ],
            hidden_projects=[
                _record(
                    id=dataset_project_id,
                    name=dataset_project_name,
                    created=created,
                ),
            ],
            tasks=[
                _record(
                    id="dataset-1",
                    project=dataset_project_id,
                    name="semiconductor-quality-data",
                    created=created,
                    system_tags=["dataset"],
                    runtime={"version": "1.0.0"},
                    status="completed",
                    type="data_processing",
                ),
                _record(
                    id="dataset-2",
                    project=dataset_project_id,
                    name="semiconductor-quality-data",
                    created=created,
                    system_tags=["dataset"],
                    runtime={"version": "2.0.0"},
                    status="completed",
                    type="data_processing",
                ),
            ],
            models=[],
        )

        report = render_status(collect_status(client, "http://localhost:8008"))

        self.assertIn("Project: 1件", report)
        self.assertIn("Task: 2件", report)
        self.assertIn("現在のProjectデータは1件あります。", report)
        self.assertIn("現在のDatasetデータは2件あります。", report)
        self.assertIn("version: 1.0.0", report)
        self.assertIn("version: 2.0.0", report)
        self.assertIn(f"Project: {dataset_project_name}", report)
        self.assertIn("現在のTraining Taskデータはありません。", report)
        self.assertIn("現在のその他のTaskデータはありません。", report)


def _client(*, projects, tasks, models, hidden_projects=()):
    client = SimpleNamespace()
    hidden_projects_by_id = {
        str(project.id): project for project in hidden_projects
    }
    client.projects = SimpleNamespace(
        get_all=_paged(projects),
        get_by_id=Mock(
            side_effect=lambda *, project: hidden_projects_by_id.get(str(project))
        ),
    )
    client.tasks = SimpleNamespace(get_all=_paged(tasks))
    client.models = SimpleNamespace(get_all=_paged(models))
    return client


def _paged(records):
    fetch = Mock()
    fetch.return_value = records
    return fetch


def _record(**values):
    defaults = {
        "id": "id",
        "name": "name",
        "project": "project",
        "created": None,
        "system_tags": [],
        "runtime": {},
        "status": None,
        "type": None,
        "framework": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


if __name__ == "__main__":
    unittest.main()
