from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from ml.semiconductor_quality import train as train_module
from ml.semiconductor_quality.config import (
    DatasetConfig,
    RandomForestConfig,
    SplitConfig,
    TrainingConfig,
)
from ml.semiconductor_quality.domain import (
    CATEGORICAL_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    DatasetSource,
    DatasetValidationReport,
    TrainingInput,
)
from ml.semiconductor_quality.preprocess import NUMERIC_TRANSFORMER
from ml.semiconductor_quality.train import (
    CLASSIFIER_STEP,
    MODEL_FILE_NAME,
    PREPROCESSOR_STEP,
    build_classifier,
    build_pipeline,
    saved_pipeline,
    train_classifier,
)


SEED = 20260906
EQUIPMENT = ("EQ-01", "EQ-02")
PROCESS_STEPS = ("ETCH", "CVD")

# The first numeric column carries the row number, so the rows the pipeline was
# fitted on can be told apart from the rows it was never allowed to see.
ROW_NUMBER_COLUMN = 0


def build_config(**forest_parameters: object) -> TrainingConfig:
    return TrainingConfig(
        dataset=DatasetConfig(dataset_version="1.0.0"),
        split=SplitConfig(),
        forest=RandomForestConfig(n_estimators=10, **forest_parameters),
        random_seed=SEED,
    )


def build_training_input(pass_rows: int = 60, fail_rows: int = 40) -> TrainingInput:
    """Build a learnable input whose rows are told apart by their row number."""
    generator = np.random.default_rng(7)
    targets = np.array(["pass"] * pass_rows + ["fail"] * fail_rows)
    features = np.empty((targets.size, len(FEATURE_COLUMNS)), dtype=object)
    for row, target in enumerate(targets):
        shift = 5.0 if target == "fail" else 0.0
        measurements = generator.normal(loc=shift, scale=1.0, size=len(NUMERIC_FEATURE_COLUMNS) - 1)
        features[row] = (
            float(row),
            *(float(value) for value in measurements),
            EQUIPMENT[row % len(EQUIPMENT)],
            PROCESS_STEPS[row % len(PROCESS_STEPS)],
        )
    report = DatasetValidationReport(
        source=DatasetSource(
            dataset_id="dataset-id",
            dataset_project="Semiconductor Quality Prediction",
            dataset_name="semiconductor-quality-data",
            dataset_version="1.0.0",
            csv_path=Path("/cache/semiconductor_quality.csv"),
        ),
        row_count=targets.size,
        feature_names=FEATURE_COLUMNS,
        numeric_feature_names=NUMERIC_FEATURE_COLUMNS,
        categorical_feature_names=CATEGORICAL_FEATURE_COLUMNS,
        label_counts={"pass": pass_rows, "fail": fail_rows},
    )
    return TrainingInput(report=report, features=features, targets=targets)


def row_numbers(features: np.ndarray) -> list[int]:
    return sorted(int(value) for value in features[:, ROW_NUMBER_COLUMN])


class RecordingPipeline:
    """Stand-in for the pipeline that records which rows the use case handed it."""

    def __init__(self) -> None:
        self.fitted_with: list[np.ndarray] = []
        self.predicted_with: list[np.ndarray] = []

    def fit(self, features: np.ndarray, targets: np.ndarray) -> "RecordingPipeline":
        self.fitted_with.append(features)
        return self

    def predict(self, features: np.ndarray) -> np.ndarray:
        self.predicted_with.append(features)
        return np.array(["pass"] * features.shape[0])


class TrainIndependenceTest(unittest.TestCase):
    def test_the_training_does_not_import_the_clearml_sdk(self) -> None:
        source = Path(train_module.__file__).read_text(encoding="utf-8")

        self.assertNotIn("import clearml", source)
        self.assertNotIn("from clearml", source)


class PipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.report = build_training_input().report

    def test_the_preprocessing_and_the_forest_are_one_pipeline(self) -> None:
        pipeline = build_pipeline(self.report, RandomForestConfig(), SEED)

        self.assertEqual(list(pipeline.named_steps), [PREPROCESSOR_STEP, CLASSIFIER_STEP])
        self.assertIsInstance(pipeline.named_steps[CLASSIFIER_STEP], RandomForestClassifier)

    def test_the_forest_is_built_from_the_execution_contract(self) -> None:
        forest = RandomForestConfig(n_estimators=150, max_depth=8, min_samples_leaf=2)

        classifier = build_classifier(forest, SEED)

        self.assertEqual(classifier.n_estimators, 150)
        self.assertEqual(classifier.max_depth, 8)
        self.assertEqual(classifier.min_samples_leaf, 2)

    def test_the_forest_shares_the_seed_of_the_run(self) -> None:
        classifier = build_classifier(RandomForestConfig(), SEED)

        self.assertEqual(classifier.random_state, SEED)

    def test_the_trees_grow_without_a_limit_unless_a_depth_is_given(self) -> None:
        classifier = build_classifier(RandomForestConfig(), SEED)

        self.assertIsNone(classifier.max_depth)


class TrainingBoundaryTest(unittest.TestCase):
    """Checks which rows the training use case is allowed to touch."""

    def setUp(self) -> None:
        self.training_input = build_training_input()
        self.pipeline = RecordingPipeline()
        patcher = mock.patch.object(
            train_module,
            "build_pipeline",
            return_value=self.pipeline,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.model = train_classifier(self.training_input, build_config())

    def test_the_pipeline_is_fitted_once_on_the_training_rows_only(self) -> None:
        self.assertEqual(len(self.pipeline.fitted_with), 1)
        self.assertEqual(
            row_numbers(self.pipeline.fitted_with[0]),
            row_numbers(self.model.split.train.features),
        )

    def test_the_validation_rows_are_kept_out_of_the_fit(self) -> None:
        fitted = set(row_numbers(self.pipeline.fitted_with[0]))

        self.assertFalse(fitted & set(row_numbers(self.model.split.validation.features)))

    def test_the_settings_are_confirmed_on_the_validation_rows(self) -> None:
        self.assertEqual(len(self.pipeline.predicted_with), 1)
        self.assertEqual(
            row_numbers(self.pipeline.predicted_with[0]),
            row_numbers(self.model.split.validation.features),
        )
        self.assertEqual(
            self.model.validation_predictions.shape[0],
            self.model.split.validation.row_count,
        )

    def test_the_test_rows_are_neither_fitted_nor_predicted(self) -> None:
        test_rows = set(row_numbers(self.model.split.test.features))
        touched = self.pipeline.fitted_with + self.pipeline.predicted_with

        for features in touched:
            self.assertFalse(test_rows & set(row_numbers(features)))

    def test_the_test_rows_are_predicted_only_when_the_final_evaluation_asks(self) -> None:
        self.model.predict(self.model.split.test)

        self.assertEqual(
            row_numbers(self.pipeline.predicted_with[-1]),
            row_numbers(self.model.split.test.features),
        )


class FittedModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.training_input = build_training_input()
        self.model = train_classifier(self.training_input, build_config())

    def test_the_fitted_model_keeps_the_dataset_it_learned_from(self) -> None:
        self.assertIs(self.model.report, self.training_input.report)

    def test_the_preprocessing_is_fitted_on_the_training_rows_only(self) -> None:
        scaler = self.model.pipeline.named_steps[PREPROCESSOR_STEP].named_transformers_[
            NUMERIC_TRANSFORMER
        ]
        train_mean = _numeric_mean(self.model.split.train.features)

        self.assertIsInstance(scaler, StandardScaler)
        np.testing.assert_allclose(scaler.mean_, train_mean)

    def test_the_preprocessing_does_not_see_the_whole_input(self) -> None:
        scaler = self.model.pipeline.named_steps[PREPROCESSOR_STEP].named_transformers_[
            NUMERIC_TRANSFORMER
        ]

        self.assertFalse(
            np.allclose(scaler.mean_, _numeric_mean(self.training_input.features)),
        )

    def test_the_fitted_model_predicts_the_labels_of_the_contract(self) -> None:
        predictions = self.model.predict(self.model.split.test)

        self.assertEqual(predictions.shape[0], self.model.split.test.row_count)
        self.assertTrue(set(predictions) <= {"pass", "fail"})

    def test_the_forest_learned_the_signal_of_the_input(self) -> None:
        predictions = self.model.predict(self.model.split.test)

        correct = np.sum(predictions == self.model.split.test.targets)
        self.assertGreater(correct / self.model.split.test.row_count, 0.8)


class ReproducibilityTest(unittest.TestCase):
    def test_the_same_contract_repeats_the_run(self) -> None:
        training_input = build_training_input()

        first = train_classifier(training_input, build_config())
        second = train_classifier(training_input, build_config())

        np.testing.assert_array_equal(
            first.validation_predictions,
            second.validation_predictions,
        )
        np.testing.assert_array_equal(
            first.predict(first.split.test),
            second.predict(second.split.test),
        )

    def test_another_seed_creates_another_run(self) -> None:
        training_input = build_training_input()
        other = TrainingConfig(
            dataset=DatasetConfig(dataset_version="1.0.0"),
            forest=RandomForestConfig(n_estimators=10),
            random_seed=SEED + 1,
        )

        first = train_classifier(training_input, build_config())
        second = train_classifier(training_input, other)

        self.assertNotEqual(
            row_numbers(first.split.test.features),
            row_numbers(second.split.test.features),
        )


class SavedPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.training_input = build_training_input()
        self.model = train_classifier(self.training_input, build_config())

    def test_the_saved_file_carries_the_preprocessing_and_the_forest(self) -> None:
        with saved_pipeline(self.model.pipeline) as weights:
            restored = joblib.load(weights)

        self.assertEqual(list(restored.named_steps), [PREPROCESSOR_STEP, CLASSIFIER_STEP])

    def test_the_saved_model_repeats_the_predictions_of_the_fitted_one(self) -> None:
        test = self.model.split.test

        with saved_pipeline(self.model.pipeline) as weights:
            restored = joblib.load(weights)

        np.testing.assert_array_equal(restored.predict(test.features), self.model.predict(test))

    def test_the_file_is_named_after_the_model_it_holds(self) -> None:
        with saved_pipeline(self.model.pipeline) as weights:
            self.assertEqual(weights.name, MODEL_FILE_NAME)
            self.assertTrue(weights.is_file())

    def test_the_file_only_lives_as_long_as_the_handover(self) -> None:
        with saved_pipeline(self.model.pipeline) as weights:
            directory = weights.parent

        self.assertFalse(weights.exists())
        self.assertFalse(directory.exists())


def _numeric_mean(features: np.ndarray) -> np.ndarray:
    return np.asarray(features[:, : len(NUMERIC_FEATURE_COLUMNS)], dtype=float).mean(axis=0)


if __name__ == "__main__":
    unittest.main()
