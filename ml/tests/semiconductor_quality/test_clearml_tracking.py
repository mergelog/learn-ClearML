from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from clearml import Task as ClearmlTask

from ml.semiconductor_quality import clearml_tracking
from ml.semiconductor_quality.clearml_tracking import (
    CONFUSION_MATRIX_TITLE,
    DATA_VALIDATION_ARTIFACT,
    DATASET_SECTION,
    DISABLED_MODEL_FRAMEWORKS,
    EVALUATION_ARTIFACT,
    EXECUTION_SECTION,
    FOREST_SECTION,
    METRICS_ITERATION,
    MODEL_LABEL_ENUMERATION,
    MODEL_NAME,
    REQUIREMENTS_FILE,
    RESOLVED_DATASET_SECTION,
    SPLIT_SECTION,
    fetch_dataset,
    start_training_task,
    training_task,
)
from ml.semiconductor_quality.config import (
    DEFAULT_DATASET_ALIAS,
    DEFAULT_DATASET_NAME,
    DEFAULT_DATASET_PROJECT,
    DEFAULT_FILES_HOST,
    DEFAULT_RANDOM_SEED,
    DEFAULT_TASK_NAME,
    DEFAULT_TASK_PROJECT,
    ClearmlSettings,
    ConfigurationError,
    DatasetConfig,
    SplitConfig,
    TrainingConfig,
)
from ml.semiconductor_quality.domain import (
    CATEGORICAL_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    LABELS,
    NUMERIC_FEATURE_COLUMNS,
    TEST_SPLIT,
    TRAIN_SPLIT,
    VALIDATION_SPLIT,
    DataSplit,
    DatasetSource,
    DatasetValidationReport,
    EvaluationResult,
    SplitPart,
    TrainingEvaluation,
)


CREDENTIAL_ENVIRONMENT = {
    "CLEARML_API_ACCESS_KEY": "access-key-value",
    "CLEARML_API_SECRET_KEY": "secret-key-value",
}


def build_config(**overrides: object) -> TrainingConfig:
    defaults: dict[str, object] = {"dataset": DatasetConfig(dataset_version="1.0.0")}
    defaults.update(overrides)
    return TrainingConfig(**defaults)  # type: ignore[arg-type]


def build_source() -> DatasetSource:
    return DatasetSource(
        dataset_id="dataset-id",
        dataset_project=DEFAULT_DATASET_PROJECT,
        dataset_name=DEFAULT_DATASET_NAME,
        dataset_version="1.0.0",
        csv_path=Path("/cache/datasets/dataset-id/semiconductor_quality.csv"),
    )


def build_report() -> DatasetValidationReport:
    return DatasetValidationReport(
        source=build_source(),
        row_count=1_200,
        feature_names=FEATURE_COLUMNS,
        numeric_feature_names=NUMERIC_FEATURE_COLUMNS,
        categorical_feature_names=CATEGORICAL_FEATURE_COLUMNS,
        label_counts={"pass": 700, "fail": 500},
    )


def build_part(name: str, pass_rows: int, fail_rows: int) -> SplitPart:
    targets = np.array(["pass"] * pass_rows + ["fail"] * fail_rows)
    return SplitPart(
        name=name,
        features=np.zeros((targets.size, len(FEATURE_COLUMNS))),
        targets=targets,
        label_counts={"pass": pass_rows, "fail": fail_rows},
    )


def build_split() -> DataSplit:
    return DataSplit(
        train=build_part(TRAIN_SPLIT, 420, 300),
        validation=build_part(VALIDATION_SPLIT, 140, 100),
        test=build_part(TEST_SPLIT, 140, 100),
    )


def build_evaluation() -> TrainingEvaluation:
    return TrainingEvaluation(
        validation=EvaluationResult(
            split_name=VALIDATION_SPLIT,
            metrics={"accuracy": 0.8125, "precision": 0.75, "recall": 0.7, "f1": 0.724},
            confusion_matrix=np.array([[120, 20], [25, 75]]),
        ),
        test=EvaluationResult(
            split_name=TEST_SPLIT,
            metrics={"accuracy": 0.7917, "precision": 0.72, "recall": 0.68, "f1": 0.699},
            confusion_matrix=np.array([[115, 25], [32, 68]]),
        ),
    )


class ClearmlSdkTestCase(unittest.TestCase):
    """Replaces the ClearML SDK entry point, so no server is contacted."""

    def setUp(self) -> None:
        self.task = mock.MagicMock(name="task")
        self.task.id = "task-id"
        self.sdk = mock.MagicMock(name="Task")
        self.sdk.TaskTypes = ClearmlTask.TaskTypes
        self.sdk.init.return_value = self.task
        self.enter_patch(mock.patch.object(clearml_tracking, "Task", self.sdk))
        self.enter_patch(mock.patch.dict("os.environ", {}, clear=True))

    def enter_patch(self, patcher: object) -> None:
        patcher.start()  # type: ignore[attr-defined]
        self.addCleanup(patcher.stop)  # type: ignore[attr-defined]

    def patch_dataset_sdk(self) -> mock.MagicMock:
        """Replace the Dataset entry point of the SDK with a resolved dataset."""
        dataset = mock.MagicMock(name="dataset")
        dataset.id = "dataset-id"
        dataset.name = "semiconductor-quality-data"
        dataset.version = "1.0.0"
        dataset.get_local_copy.return_value = "/cache/datasets/dataset-id"
        sdk = mock.MagicMock(name="Dataset")
        sdk.get.return_value = dataset
        self.enter_patch(mock.patch.object(clearml_tracking, "Dataset", sdk))
        return sdk

    @property
    def init_arguments(self) -> dict[str, object]:
        self.sdk.init.assert_called_once()
        return self.sdk.init.call_args.kwargs

    def recorded_parameters(self) -> dict[str, dict[str, object]]:
        return {
            call.kwargs["name"]: call.args[0] for call in self.task.connect.call_args_list
        }

    def uploaded_artifacts(self) -> dict[str, dict[str, object]]:
        return {
            call.args[0]: call.kwargs["artifact_object"]
            for call in self.task.upload_artifact.call_args_list
        }

    def reported_scalars(self) -> dict[tuple[str, str], float]:
        logger = self.task.get_logger.return_value
        return {
            (call.kwargs["title"], call.kwargs["series"]): call.kwargs["value"]
            for call in logger.report_scalar.call_args_list
        }

    def patch_output_model(self) -> mock.MagicMock:
        """Replace the Output Model entry point, so no model is uploaded."""
        sdk = mock.MagicMock(name="OutputModel")
        self.enter_patch(mock.patch.object(clearml_tracking, "OutputModel", sdk))
        return sdk


class StartTrainingTaskTest(ClearmlSdkTestCase):
    def test_a_new_task_is_forced_for_every_execution(self) -> None:
        start_training_task(build_config())

        self.assertIs(self.init_arguments["reuse_last_task_id"], False)

    def test_scikit_and_joblib_model_tracking_is_disabled(self) -> None:
        start_training_task(build_config())

        self.assertEqual(
            self.init_arguments["auto_connect_frameworks"],
            {"scikit": False, "joblib": False},
        )
        self.assertEqual(dict(DISABLED_MODEL_FRAMEWORKS), {"scikit": False, "joblib": False})

    def test_the_command_line_is_not_connected_twice(self) -> None:
        start_training_task(build_config())

        self.assertIs(self.init_arguments["auto_connect_arg_parser"], False)

    def test_the_task_is_created_in_the_task_project(self) -> None:
        start_training_task(build_config())

        arguments = self.init_arguments
        self.assertEqual(arguments["project_name"], DEFAULT_TASK_PROJECT)
        self.assertNotEqual(arguments["project_name"], DEFAULT_DATASET_PROJECT)
        self.assertEqual(arguments["task_name"], DEFAULT_TASK_NAME)
        self.assertEqual(arguments["task_type"], ClearmlTask.TaskTypes.training)

    def test_output_is_stored_on_the_configured_files_server(self) -> None:
        start_training_task(build_config())

        self.assertEqual(self.init_arguments["output_uri"], DEFAULT_FILES_HOST)

    def test_the_started_task_exposes_its_id(self) -> None:
        started = start_training_task(build_config())

        self.assertEqual(started.id, "task-id")

    def test_dependencies_are_recorded_once_immediately_after_task_init(self) -> None:
        events: list[str] = []
        self.sdk.init.side_effect = lambda **_: events.append("task-init") or self.task
        self.task.set_packages.side_effect = lambda _: events.append("set-packages")
        self.task.connect.side_effect = lambda *_args, **_kwargs: events.append("connect")

        start_training_task(build_config())

        self.task.set_packages.assert_called_once_with(str(REQUIREMENTS_FILE))
        self.assertEqual(events[:3], ["task-init", "set-packages", "connect"])

    def test_requirements_file_is_resolved_independently_of_working_directory(
        self,
    ) -> None:
        start_training_task(build_config())

        requirements_file = Path(self.task.set_packages.call_args.args[0])
        self.assertTrue(requirements_file.is_absolute())
        expected = Path(__file__).resolve().parents[3] / "tools" / "requirements.txt"
        self.assertEqual(requirements_file, expected)
        self.assertTrue(requirements_file.is_file())

    def test_the_server_is_configured_before_the_task_is_created(self) -> None:
        with mock.patch.dict("os.environ", CREDENTIAL_ENVIRONMENT):
            start_training_task(build_config())

        called = [call[0] for call in self.sdk.mock_calls]
        self.assertLess(called.index("set_credentials"), called.index("init"))
        self.assertEqual(
            self.sdk.set_credentials.call_args.kwargs["key"],
            "access-key-value",
        )

    def test_credentials_may_be_left_to_the_sdk_configuration(self) -> None:
        start_training_task(build_config())

        arguments = self.sdk.set_credentials.call_args.kwargs
        self.assertIsNone(arguments["key"])
        self.assertIsNone(arguments["secret"])

    def test_an_invalid_configuration_is_rejected_before_the_task_is_created(self) -> None:
        config = build_config(dataset=DatasetConfig(dataset_version=" "))

        with self.assertRaises(ConfigurationError):
            start_training_task(config)

        self.sdk.init.assert_not_called()

    def test_invalid_settings_are_rejected_before_the_task_is_created(self) -> None:
        settings = ClearmlSettings(access_key="access-key-value")

        with self.assertRaises(ConfigurationError):
            start_training_task(build_config(), settings=settings)

        self.sdk.init.assert_not_called()


class ParameterTrackingTest(ClearmlSdkTestCase):
    def test_the_resolved_contract_is_recorded_as_parameters(self) -> None:
        config = build_config(
            dataset=DatasetConfig(dataset_version="2.0.0"),
            split=SplitConfig(train_ratio=0.5, validation_ratio=0.25, test_ratio=0.25),
        )

        start_training_task(config)

        parameters = self.recorded_parameters()
        self.assertEqual(parameters[DATASET_SECTION]["dataset_version"], "2.0.0")
        self.assertEqual(parameters[DATASET_SECTION]["dataset_alias"], config.dataset.dataset_alias)
        self.assertEqual(parameters[SPLIT_SECTION]["train_ratio"], 0.5)
        self.assertEqual(parameters[FOREST_SECTION]["n_estimators"], config.forest.n_estimators)
        self.assertEqual(parameters[EXECUTION_SECTION]["random_seed"], DEFAULT_RANDOM_SEED)

    def test_the_command_line_is_recorded_as_given(self) -> None:
        start_training_task(
            build_config(),
            command_line=("--dataset-version", "1.0.0", "--task-name", "run one"),
        )

        parameters = self.recorded_parameters()
        self.assertEqual(
            parameters[EXECUTION_SECTION]["command_line"],
            "--dataset-version 1.0.0 --task-name 'run one'",
        )

    def test_an_execution_without_arguments_records_an_empty_command_line(self) -> None:
        start_training_task(build_config())

        self.assertEqual(self.recorded_parameters()[EXECUTION_SECTION]["command_line"], "")

    def test_credentials_are_never_recorded_as_parameters(self) -> None:
        with mock.patch.dict("os.environ", CREDENTIAL_ENVIRONMENT):
            start_training_task(build_config(), command_line=("--dataset-version", "1.0.0"))

        recorded = str(self.recorded_parameters())
        self.assertNotIn("access-key-value", recorded)
        self.assertNotIn("secret-key-value", recorded)


class FetchDatasetTest(ClearmlSdkTestCase):
    def test_the_requested_version_is_resolved_and_never_inferred(self) -> None:
        sdk = self.patch_dataset_sdk()

        fetch_dataset(DatasetConfig(dataset_version="2.0.0"))

        arguments = sdk.get.call_args.kwargs
        self.assertEqual(arguments["dataset_project"], DEFAULT_DATASET_PROJECT)
        self.assertEqual(arguments["dataset_name"], DEFAULT_DATASET_NAME)
        self.assertEqual(arguments["dataset_version"], "2.0.0")
        self.assertIs(arguments["only_completed"], True)

    def test_the_dataset_is_linked_to_the_running_task_by_its_alias(self) -> None:
        sdk = self.patch_dataset_sdk()

        fetch_dataset(DatasetConfig(dataset_version="1.0.0"))

        self.assertEqual(sdk.get.call_args.kwargs["alias"], DEFAULT_DATASET_ALIAS)

    def test_the_read_only_cache_of_the_resolved_version_is_downloaded(self) -> None:
        sdk = self.patch_dataset_sdk()

        fetched = fetch_dataset(DatasetConfig(dataset_version="1.0.0"))

        sdk.get.return_value.get_local_copy.assert_called_once_with()
        self.assertEqual(fetched.local_root, Path("/cache/datasets/dataset-id"))

    def test_the_resolved_identity_comes_from_the_dataset_itself(self) -> None:
        self.patch_dataset_sdk()

        fetched = fetch_dataset(DatasetConfig(dataset_version="1.0.0"))

        self.assertEqual(fetched.dataset_id, "dataset-id")
        self.assertEqual(fetched.dataset_name, "semiconductor-quality-data")
        self.assertEqual(fetched.dataset_version, "1.0.0")
        self.assertEqual(fetched.dataset_project, DEFAULT_DATASET_PROJECT)

    def test_the_requested_version_is_kept_when_the_server_reports_none(self) -> None:
        sdk = self.patch_dataset_sdk()
        sdk.get.return_value.version = None

        fetched = fetch_dataset(DatasetConfig(dataset_version="1.0.0"))

        self.assertEqual(fetched.dataset_version, "1.0.0")

    def test_the_dataset_is_fetched_only_after_the_task_exists(self) -> None:
        sdk = self.patch_dataset_sdk()
        events: list[str] = []
        self.sdk.init.side_effect = lambda **_: events.append("task-init") or self.task
        sdk.get.side_effect = lambda **_: events.append("dataset-get") or sdk.get.return_value

        with training_task(build_config()):
            fetch_dataset(DatasetConfig(dataset_version="1.0.0"))

        self.assertEqual(events, ["task-init", "dataset-get"])


class DatasetSourceTrackingTest(ClearmlSdkTestCase):
    def test_the_resolved_dataset_is_recorded_next_to_the_requested_one(self) -> None:
        started = start_training_task(build_config())

        started.record_dataset_source(
            DatasetSource(
                dataset_id="dataset-id",
                dataset_project=DEFAULT_DATASET_PROJECT,
                dataset_name=DEFAULT_DATASET_NAME,
                dataset_version="1.0.0",
                csv_path=Path("/cache/datasets/dataset-id/semiconductor_quality.csv"),
            )
        )

        parameters = self.recorded_parameters()
        resolved = parameters[RESOLVED_DATASET_SECTION]
        self.assertEqual(resolved["dataset_id"], "dataset-id")
        self.assertEqual(resolved["dataset_version"], "1.0.0")
        self.assertEqual(resolved["dataset_name"], DEFAULT_DATASET_NAME)
        self.assertEqual(
            resolved["csv_path"],
            "/cache/datasets/dataset-id/semiconductor_quality.csv",
        )
        self.assertIn(DATASET_SECTION, parameters)


class TrainingBoundaryTest(ClearmlSdkTestCase):
    def test_the_task_is_started_before_the_dataset_is_read(self) -> None:
        events: list[str] = []
        self.sdk.init.side_effect = lambda **_: events.append("task-init") or self.task

        with training_task(build_config()):
            events.append("dataset-get")

        self.assertEqual(events, ["task-init", "dataset-get"])

    def test_a_successful_run_waits_for_uploads_before_closing(self) -> None:
        with training_task(build_config()):
            pass

        self.task.flush.assert_called_once_with(wait_for_uploads=True)
        self.task.close.assert_called_once_with()
        self.task.mark_failed.assert_not_called()

    def test_a_failure_after_the_task_started_is_tracked_as_a_failed_task(self) -> None:
        with self.assertRaises(RuntimeError):
            with training_task(build_config()):
                raise RuntimeError("dataset 1.0.0 was not found")

        arguments = self.task.mark_failed.call_args.kwargs
        self.assertEqual(arguments["status_reason"], "RuntimeError")
        self.assertEqual(arguments["status_message"], "dataset 1.0.0 was not found")
        self.assertIs(arguments["force"], True)
        self.task.close.assert_called_once_with()

    def test_the_reason_of_a_failure_is_left_on_the_task_log(self) -> None:
        with self.assertRaises(ValueError):
            with training_task(build_config()):
                raise ValueError("result column is missing")

        reported = self.task.get_logger.return_value.report_text.call_args.args[0]
        self.assertIn("result column is missing", reported)

    def test_a_failed_run_is_never_completed(self) -> None:
        with self.assertRaises(RuntimeError):
            with training_task(build_config()):
                raise RuntimeError("boom")

        self.task.mark_completed.assert_not_called()
        self.task.flush.assert_not_called()

    def test_a_manually_interrupted_run_is_left_to_the_sdk(self) -> None:
        with self.assertRaises(KeyboardInterrupt):
            with training_task(build_config()):
                raise KeyboardInterrupt

        self.task.mark_failed.assert_not_called()
        self.task.close.assert_not_called()

    def test_the_task_is_closed_once(self) -> None:
        started = start_training_task(build_config())

        started.complete()
        started.complete()
        started.fail(RuntimeError("boom"))

        self.task.close.assert_called_once_with()
        self.task.mark_failed.assert_not_called()


class InputTrackingTest(ClearmlSdkTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.started = start_training_task(build_config())
        self.started.record_input(build_report(), build_split())
        self.payload = self.uploaded_artifacts()[DATA_VALIDATION_ARTIFACT]

    def test_the_dataset_the_run_learned_from_is_part_of_the_payload(self) -> None:
        self.assertEqual(self.payload["dataset"]["id"], "dataset-id")
        self.assertEqual(self.payload["dataset"]["version"], "1.0.0")
        self.assertEqual(self.payload["row_count"], 1_200)
        self.assertEqual(self.payload["label_counts"], {"pass": 700, "fail": 500})

    def test_the_columns_a_model_was_allowed_to_see_are_recorded(self) -> None:
        features = self.payload["features"]

        self.assertEqual(features["all"], list(FEATURE_COLUMNS))
        self.assertEqual(features["numeric"], list(NUMERIC_FEATURE_COLUMNS))
        self.assertEqual(features["categorical"], list(CATEGORICAL_FEATURE_COLUMNS))
        self.assertNotIn("sample_id", features["all"])
        self.assertNotIn("result", features["all"])

    def test_the_composition_of_every_part_is_recorded(self) -> None:
        split = self.payload["split"]

        self.assertEqual(list(split), [TRAIN_SPLIT, VALIDATION_SPLIT, TEST_SPLIT])
        self.assertEqual(split[TRAIN_SPLIT]["row_count"], 720)
        self.assertEqual(split[TEST_SPLIT]["label_counts"], {"pass": 140, "fail": 100})


class EvaluationTrackingTest(ClearmlSdkTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.evaluation = build_evaluation()
        self.started = start_training_task(build_config())
        self.started.record_evaluation(self.evaluation)
        self.logger = self.task.get_logger.return_value

    def test_the_validation_and_the_test_are_reported_as_separate_series(self) -> None:
        scalars = self.reported_scalars()

        self.assertEqual(scalars[("accuracy", VALIDATION_SPLIT)], 0.8125)
        self.assertEqual(scalars[("accuracy", TEST_SPLIT)], 0.7917)
        self.assertEqual(scalars[("recall", VALIDATION_SPLIT)], 0.7)
        self.assertEqual(scalars[("recall", TEST_SPLIT)], 0.68)

    def test_every_metric_of_a_scored_split_is_reported(self) -> None:
        reported = {
            title for title, series in self.reported_scalars() if series == TEST_SPLIT
        }

        self.assertEqual(reported, set(self.evaluation.test.metrics))

    def test_the_final_figures_of_a_run_share_one_iteration(self) -> None:
        iterations = {
            call.kwargs["iteration"] for call in self.logger.report_scalar.call_args_list
        }

        self.assertEqual(iterations, {METRICS_ITERATION})

    def test_a_confusion_matrix_is_reported_for_every_scored_split(self) -> None:
        matrices = {
            call.kwargs["series"]: call.kwargs["matrix"]
            for call in self.logger.report_confusion_matrix.call_args_list
        }

        self.assertEqual(set(matrices), {VALIDATION_SPLIT, TEST_SPLIT})
        np.testing.assert_array_equal(matrices[TEST_SPLIT], self.evaluation.test.confusion_matrix)

    def test_the_confusion_matrix_states_which_axis_is_the_actual_label(self) -> None:
        arguments = self.logger.report_confusion_matrix.call_args.kwargs

        self.assertEqual(arguments["title"], CONFUSION_MATRIX_TITLE)
        self.assertEqual(arguments["xlabels"], list(LABELS))
        self.assertEqual(arguments["ylabels"], list(LABELS))
        self.assertIn("actual", arguments["comment"])

    def test_the_scored_splits_are_kept_as_one_json_artifact(self) -> None:
        payload = self.uploaded_artifacts()[EVALUATION_ARTIFACT]

        self.assertEqual(list(payload), [VALIDATION_SPLIT, TEST_SPLIT])
        self.assertEqual(payload[TEST_SPLIT]["metrics"], dict(self.evaluation.test.metrics))
        self.assertEqual(payload[TEST_SPLIT]["labels"], list(LABELS))
        self.assertEqual(payload[TEST_SPLIT]["confusion_matrix"], [[115, 25], [32, 68]])

    def test_an_artifact_is_readable_json_and_is_awaited(self) -> None:
        arguments = self.task.upload_artifact.call_args.kwargs

        self.assertIs(arguments["wait_on_upload"], True)
        self.assertIs(arguments["auto_pickle"], False)


class ModelRegistrationTest(ClearmlSdkTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.output_model = self.patch_output_model()
        self.started = start_training_task(build_config())
        self.started.register_model(Path("/tmp/run/semiconductor_quality_pipeline.joblib"))

    def test_the_model_belongs_to_the_task_that_fitted_it(self) -> None:
        arguments = self.output_model.call_args.kwargs

        self.assertIs(arguments["task"], self.task)
        self.assertEqual(arguments["name"], MODEL_NAME)
        self.assertEqual(arguments["label_enumeration"], dict(MODEL_LABEL_ENUMERATION))

    def test_the_saved_pipeline_is_uploaded_before_the_file_is_released(self) -> None:
        arguments = self.output_model.return_value.update_weights.call_args.kwargs

        self.assertEqual(
            arguments["weights_filename"],
            "/tmp/run/semiconductor_quality_pipeline.joblib",
        )
        self.assertIs(arguments["async_enable"], False)
        self.assertIs(arguments["auto_delete_file"], False)

    def test_the_task_registers_the_pipeline_exactly_once(self) -> None:
        self.output_model.assert_called_once()
        self.output_model.return_value.update_weights.assert_called_once()
        self.assertEqual(self.init_arguments["auto_connect_frameworks"], {"scikit": False, "joblib": False})

    def test_the_labels_are_enumerated_in_the_order_of_the_contract(self) -> None:
        self.assertEqual(dict(MODEL_LABEL_ENUMERATION), {"pass": 0, "fail": 1})


if __name__ == "__main__":
    unittest.main()
