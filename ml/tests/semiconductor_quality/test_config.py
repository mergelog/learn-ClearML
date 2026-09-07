from __future__ import annotations

import unittest
from unittest import mock

from ml.semiconductor_quality.config import (
    DEFAULT_API_HOST,
    DEFAULT_DATASET_ALIAS,
    DEFAULT_DATASET_CSV_PATH,
    DEFAULT_DATASET_NAME,
    DEFAULT_DATASET_PROJECT,
    DEFAULT_FILES_HOST,
    DEFAULT_RANDOM_SEED,
    DEFAULT_TASK_NAME,
    DEFAULT_TASK_PROJECT,
    DEFAULT_WEB_HOST,
    ClearmlSettings,
    ConfigurationError,
    DatasetConfig,
    RandomForestConfig,
    SplitConfig,
    TaskConfig,
    TrainingConfig,
)


def build_config(**overrides: object) -> TrainingConfig:
    defaults: dict[str, object] = {"dataset": DatasetConfig(dataset_version="1.0.0")}
    defaults.update(overrides)
    return TrainingConfig(**defaults)  # type: ignore[arg-type]


class DatasetConfigTest(unittest.TestCase):
    def test_defaults_match_the_registered_seed_dataset(self) -> None:
        config = DatasetConfig(dataset_version="1.0.0")

        self.assertEqual(config.dataset_project, DEFAULT_DATASET_PROJECT)
        self.assertEqual(config.dataset_name, DEFAULT_DATASET_NAME)
        self.assertEqual(config.dataset_csv_path, DEFAULT_DATASET_CSV_PATH)
        self.assertEqual(config.dataset_alias, DEFAULT_DATASET_ALIAS)
        self.assertEqual(config.collect_errors(), ())

    def test_dataset_version_has_no_default(self) -> None:
        with self.assertRaises(TypeError):
            DatasetConfig()  # type: ignore[call-arg]

    def test_blank_dataset_version_is_rejected(self) -> None:
        for version in ("", "   "):
            with self.subTest(version=version):
                errors = DatasetConfig(dataset_version=version).collect_errors()

                self.assertIn("dataset_version is required", errors)

    def test_csv_path_outside_the_dataset_root_is_rejected(self) -> None:
        rejected = ("/etc/passwd", "C:\\data\\quality.csv", "../quality.csv", "a/../../b.csv")
        for csv_path in rejected:
            with self.subTest(csv_path=csv_path):
                errors = DatasetConfig(
                    dataset_version="1.0.0",
                    dataset_csv_path=csv_path,
                ).collect_errors()

                self.assertTrue(errors, f"{csv_path!r} should be rejected")

    def test_nested_relative_csv_path_is_accepted(self) -> None:
        config = DatasetConfig(
            dataset_version="1.0.0",
            dataset_csv_path="v1.0.0/semiconductor_quality.csv",
        )

        self.assertEqual(config.collect_errors(), ())


class TaskConfigTest(unittest.TestCase):
    def test_task_project_is_separated_from_the_dataset_project(self) -> None:
        config = TaskConfig()

        self.assertEqual(config.task_project, DEFAULT_TASK_PROJECT)
        self.assertEqual(config.task_project, f"{DEFAULT_DATASET_PROJECT}/Training")
        self.assertNotEqual(config.task_project, DEFAULT_DATASET_PROJECT)
        self.assertEqual(config.task_name, DEFAULT_TASK_NAME)

    def test_blank_names_are_rejected(self) -> None:
        errors = TaskConfig(task_project=" ", task_name="").collect_errors()

        self.assertIn("task_project is required", errors)
        self.assertIn("task_name is required", errors)


class SplitConfigTest(unittest.TestCase):
    def test_default_ratios_sum_to_one(self) -> None:
        config = SplitConfig()

        self.assertEqual(config.collect_errors(), ())
        self.assertAlmostEqual(config.total_ratio, 1.0)

    def test_ratios_that_do_not_sum_to_one_are_rejected(self) -> None:
        errors = SplitConfig(
            train_ratio=0.7,
            validation_ratio=0.2,
            test_ratio=0.2,
        ).collect_errors()

        self.assertEqual(len(errors), 1)
        self.assertIn("must sum to 1.0", errors[0])

    def test_ratios_outside_the_open_unit_interval_are_rejected(self) -> None:
        errors = SplitConfig(
            train_ratio=1.0,
            validation_ratio=0.0,
            test_ratio=-0.2,
        ).collect_errors()

        self.assertEqual(len(errors), 3)

    def test_a_split_without_a_test_part_is_rejected(self) -> None:
        errors = SplitConfig(
            train_ratio=0.8,
            validation_ratio=0.2,
            test_ratio=0.0,
        ).collect_errors()

        self.assertTrue(any("test_ratio" in message for message in errors))


class RandomForestConfigTest(unittest.TestCase):
    def test_defaults_are_valid(self) -> None:
        config = RandomForestConfig()

        self.assertEqual(config.collect_errors(), ())
        self.assertIsNone(config.max_depth)

    def test_non_positive_parameters_are_rejected(self) -> None:
        errors = RandomForestConfig(
            n_estimators=0,
            max_depth=0,
            min_samples_leaf=-1,
        ).collect_errors()

        self.assertEqual(len(errors), 3)

    def test_unlimited_depth_is_accepted(self) -> None:
        self.assertEqual(RandomForestConfig(max_depth=None).collect_errors(), ())


class TrainingConfigTest(unittest.TestCase):
    def test_valid_configuration_passes_validation(self) -> None:
        config = build_config()

        self.assertIs(config.validate(), config)
        self.assertEqual(config.random_seed, DEFAULT_RANDOM_SEED)

    def test_missing_dataset_version_is_rejected_before_task_creation(self) -> None:
        config = build_config(dataset=DatasetConfig(dataset_version=""))

        with self.assertRaises(ConfigurationError) as raised:
            config.validate()

        self.assertIn("dataset_version is required", str(raised.exception))

    def test_every_problem_is_reported_at_once(self) -> None:
        config = build_config(
            dataset=DatasetConfig(dataset_version="", dataset_csv_path="/tmp/quality.csv"),
            split=SplitConfig(train_ratio=0.5, validation_ratio=0.2, test_ratio=0.2),
            forest=RandomForestConfig(n_estimators=0),
        )

        with self.assertRaises(ConfigurationError) as raised:
            config.validate()

        message = str(raised.exception)
        self.assertIn("dataset_version is required", message)
        self.assertIn("dataset_csv_path", message)
        self.assertIn("must sum to 1.0", message)
        self.assertIn("n_estimators", message)

    def test_random_seed_must_be_an_integer(self) -> None:
        config = build_config(random_seed="20260906")

        with self.assertRaises(ConfigurationError):
            config.validate()

    def test_configuration_carries_no_credentials(self) -> None:
        field_names = set(TrainingConfig.__dataclass_fields__)

        self.assertNotIn("access_key", field_names)
        self.assertNotIn("secret_key", field_names)


class ClearmlSettingsTest(unittest.TestCase):
    def test_environment_is_the_only_credential_source(self) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            settings = ClearmlSettings.from_environment()

        self.assertEqual(settings.api_host, DEFAULT_API_HOST)
        self.assertEqual(settings.web_host, DEFAULT_WEB_HOST)
        self.assertEqual(settings.files_host, DEFAULT_FILES_HOST)
        self.assertIsNone(settings.access_key)
        self.assertIsNone(settings.secret_key)
        self.assertFalse(settings.has_explicit_credentials)
        self.assertEqual(settings.collect_errors(), ())

    def test_hosts_are_read_from_the_environment_without_a_trailing_slash(self) -> None:
        environment = {
            "CLEARML_API_HOST": "http://clearml.local:8008/",
            "CLEARML_WEB_HOST": "http://clearml.local:8080/",
            "CLEARML_FILES_HOST": "http://clearml.local:8081/",
            "CLEARML_API_ACCESS_KEY": "access",
            "CLEARML_API_SECRET_KEY": "secret",
        }
        with mock.patch.dict("os.environ", environment, clear=True):
            settings = ClearmlSettings.from_environment()

        self.assertEqual(settings.api_host, "http://clearml.local:8008")
        self.assertEqual(settings.web_host, "http://clearml.local:8080")
        self.assertEqual(settings.files_host, "http://clearml.local:8081")
        self.assertTrue(settings.has_explicit_credentials)

    def test_partial_credentials_are_rejected(self) -> None:
        with mock.patch.dict("os.environ", {"CLEARML_API_ACCESS_KEY": "access"}, clear=True):
            settings = ClearmlSettings.from_environment()

        with self.assertRaises(ConfigurationError) as raised:
            settings.validate()

        self.assertIn("must be set together", str(raised.exception))

    def test_credentials_are_not_exposed_by_repr(self) -> None:
        settings = ClearmlSettings(access_key="access", secret_key="secret")

        self.assertNotIn("access", repr(settings))
        self.assertNotIn("secret", repr(settings))


if __name__ == "__main__":
    unittest.main()
