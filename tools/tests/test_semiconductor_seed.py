from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from tools.semiconductor_seed.clearml_gateway import ClearmlGateway
from tools.semiconductor_seed.config import DATASET_NAME, PROJECT_ROOT, Settings
from tools.semiconductor_seed.dataset_seeding import seed_datasets
from tools.semiconductor_seed.domain import DatasetVersion, GeneratedDataset
from tools.semiconductor_seed.generator import generate_dataset
from tools.semiconductor_seed.scenarios import experiment_specs


class RecordingDatasetGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[GeneratedDataset, str | None]] = []

    def ensure_dataset(
        self,
        dataset: GeneratedDataset,
        parent_id: str | None = None,
    ) -> str:
        self.calls.append((dataset, parent_id))
        return f"dataset-{dataset.definition.version}"


class SemiconductorDatasetGeneratorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = DatasetVersion(
            version="test",
            row_count=200,
            random_seed_offset=0,
            description="Test data",
        )

    def test_generation_is_reproducible(self) -> None:
        with (
            tempfile.TemporaryDirectory() as first_dir,
            tempfile.TemporaryDirectory() as second_dir,
        ):
            first = generate_dataset(self.definition, Path(first_dir), base_seed=123)
            second = generate_dataset(self.definition, Path(second_dir), base_seed=123)

            np.testing.assert_array_equal(first.features, second.features)
            np.testing.assert_array_equal(first.targets, second.targets)
            self.assertEqual(first.csv_path.read_bytes(), second.csv_path.read_bytes())

    def test_dataset_contains_both_classes(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            generated = generate_dataset(self.definition, Path(output_dir), base_seed=123)

            labels, counts = np.unique(generated.targets, return_counts=True)
            distribution = dict(zip(labels, counts / counts.sum(), strict=True))

            self.assertEqual(set(distribution), {"pass", "fail"})
            self.assertGreater(distribution["pass"], 0.55)
        self.assertGreater(distribution["fail"], 0.30)


class SemiconductorSeedSettingsTest(unittest.TestCase):
    def test_credentials_are_optional(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings.from_environment()

        self.assertIsNone(settings.access_key)
        self.assertIsNone(settings.secret_key)

    def test_credentials_are_read_from_environment(self) -> None:
        environment = {
            "CLEARML_API_ACCESS_KEY": "access-key",
            "CLEARML_API_SECRET_KEY": "secret-key",
        }

        with patch.dict("os.environ", environment, clear=True):
            settings = Settings.from_environment()

        self.assertEqual(settings.access_key, "access-key")
        self.assertEqual(settings.secret_key, "secret-key")
        self.assertNotIn("access-key", repr(settings))
        self.assertNotIn("secret-key", repr(settings))

    def test_incomplete_credentials_are_rejected(self) -> None:
        environment = {"CLEARML_API_ACCESS_KEY": "access-key"}

        with patch.dict("os.environ", environment, clear=True):
            with self.assertRaisesRegex(ValueError, "must be set together"):
                Settings.from_environment()


class SemiconductorDatasetSeedingTest(unittest.TestCase):
    def test_registers_only_versioned_datasets_in_parent_order(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            settings = Settings(
                api_host="http://localhost:8008",
                web_host="http://localhost:8080",
                files_host="http://localhost:8081",
                access_key="test-access-key",
                secret_key="test-secret-key",
                output_dir=Path(output_dir),
                random_seed=123,
            )
            gateway = RecordingDatasetGateway()

            datasets, dataset_ids = seed_datasets(settings, gateway)

            self.assertEqual(list(datasets), ["1.0.0", "2.0.0"])
            self.assertEqual(
                dataset_ids,
                {
                    "1.0.0": "dataset-1.0.0",
                    "2.0.0": "dataset-2.0.0",
                },
            )
            self.assertEqual(
                [
                    (dataset.definition.version, parent_id)
                    for dataset, parent_id in gateway.calls
                ],
                [
                    ("1.0.0", None),
                    ("2.0.0", "dataset-1.0.0"),
                ],
            )


class ClearmlGatewayTest(unittest.TestCase):
    @patch("tools.semiconductor_seed.clearml_gateway.Dataset.create")
    @patch("tools.semiconductor_seed.clearml_gateway.Dataset.get")
    def test_reuses_existing_dataset_without_requiring_seed_tag(
        self,
        get_mock: Mock,
        create_mock: Mock,
    ) -> None:
        existing = Mock(id="existing-dataset-id")
        get_mock.return_value = existing
        gateway = ClearmlGateway.__new__(ClearmlGateway)
        dataset = GeneratedDataset(
            definition=DatasetVersion(
                version="1.0.0",
                row_count=0,
                random_seed_offset=0,
                description="Existing dataset",
            ),
            csv_path=Path("unused.csv"),
            features=np.empty((0, 0)),
            targets=np.empty(0),
        )

        dataset_id = gateway.ensure_dataset(dataset)

        self.assertEqual(dataset_id, "existing-dataset-id")
        get_mock.assert_called_once_with(
            dataset_project=PROJECT_ROOT,
            dataset_name=DATASET_NAME,
            dataset_version="1.0.0",
            only_completed=True,
        )
        create_mock.assert_not_called()


class SemiconductorScenarioTest(unittest.TestCase):
    def test_twenty_unique_experiments_are_defined(self) -> None:
        specs = experiment_specs()

        self.assertEqual(len(specs), 20)
        self.assertEqual(len({spec.name for spec in specs}), 20)
        self.assertEqual(sum(spec.final_status == "failed" for spec in specs), 1)
        self.assertEqual(sum(spec.final_status == "aborted" for spec in specs), 1)


if __name__ == "__main__":
    unittest.main()
