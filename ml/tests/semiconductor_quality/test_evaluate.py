from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from ml.semiconductor_quality import evaluate as evaluate_module
from ml.semiconductor_quality.domain import (
    CATEGORICAL_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    LABELS,
    NUMERIC_FEATURE_COLUMNS,
    TEST_SPLIT,
    VALIDATION_SPLIT,
    DataSplit,
    DatasetSource,
    DatasetValidationReport,
    SplitPart,
)
from ml.semiconductor_quality.evaluate import (
    ACCURACY,
    F1,
    METRIC_NAMES,
    PRECISION,
    RECALL,
    EvaluationError,
    evaluate_model,
    evaluate_split,
)
from ml.semiconductor_quality.train import TrainedModel


# Four products passed and four failed. Of the four failures the model found
# two, and it wrongly rejected one good product.
TARGETS = np.array(["pass", "pass", "pass", "pass", "fail", "fail", "fail", "fail"])
PREDICTIONS = np.array(["pass", "pass", "pass", "fail", "fail", "fail", "pass", "pass"])


def build_part(name: str, targets: np.ndarray) -> SplitPart:
    return SplitPart(
        name=name,
        features=np.zeros((targets.size, len(FEATURE_COLUMNS))),
        targets=targets,
        label_counts={label: int(np.sum(targets == label)) for label in LABELS},
    )


def build_report() -> DatasetValidationReport:
    return DatasetValidationReport(
        source=DatasetSource(
            dataset_id="dataset-id",
            dataset_project="Semiconductor Quality Prediction",
            dataset_name="semiconductor-quality-data",
            dataset_version="1.0.0",
            csv_path=Path("/cache/datasets/dataset-id/semiconductor_quality.csv"),
        ),
        row_count=TARGETS.size * 2,
        feature_names=FEATURE_COLUMNS,
        numeric_feature_names=NUMERIC_FEATURE_COLUMNS,
        categorical_feature_names=CATEGORICAL_FEATURE_COLUMNS,
        label_counts={"pass": 8, "fail": 8},
    )


class CountingPipeline:
    """Stand-in for the fitted pipeline that counts what it was asked to predict."""

    def __init__(self, predictions: np.ndarray) -> None:
        self.predictions = predictions
        self.predicted_rows: list[int] = []

    def predict(self, features: np.ndarray) -> np.ndarray:
        self.predicted_rows.append(int(features.shape[0]))
        return self.predictions


class EvaluateIndependenceTest(unittest.TestCase):
    def test_the_evaluation_does_not_import_the_clearml_sdk(self) -> None:
        source = Path(evaluate_module.__file__).read_text(encoding="utf-8")

        self.assertNotIn("import clearml", source)
        self.assertNotIn("from clearml", source)


class MetricsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.result = evaluate_split(build_part(TEST_SPLIT, TARGETS), PREDICTIONS)

    def test_every_metric_of_the_contract_is_measured(self) -> None:
        self.assertEqual(tuple(self.result.metrics), METRIC_NAMES)

    def test_the_share_of_correct_predictions_is_the_accuracy(self) -> None:
        self.assertAlmostEqual(self.result.metrics[ACCURACY], 5 / 8)

    def test_precision_and_recall_describe_the_failing_products(self) -> None:
        self.assertAlmostEqual(self.result.metrics[PRECISION], 2 / 3)
        self.assertAlmostEqual(self.result.metrics[RECALL], 2 / 4)

    def test_the_f1_balances_precision_and_recall(self) -> None:
        self.assertAlmostEqual(self.result.metrics[F1], 2 * (2 / 3) * 0.5 / ((2 / 3) + 0.5))

    def test_a_run_that_never_predicts_a_failure_scores_zero_instead_of_failing(self) -> None:
        result = evaluate_split(
            build_part(TEST_SPLIT, TARGETS),
            np.array(["pass"] * TARGETS.size),
        )

        self.assertEqual(result.metrics[PRECISION], 0.0)
        self.assertEqual(result.metrics[RECALL], 0.0)
        self.assertEqual(result.metrics[F1], 0.0)

    def test_the_metrics_are_plain_numbers(self) -> None:
        for value in self.result.metrics.values():
            self.assertIsInstance(value, float)


class ConfusionMatrixTest(unittest.TestCase):
    def setUp(self) -> None:
        self.result = evaluate_split(build_part(TEST_SPLIT, TARGETS), PREDICTIONS)

    def test_the_rows_are_the_actual_labels_and_the_columns_the_predicted_ones(self) -> None:
        np.testing.assert_array_equal(self.result.confusion_matrix, np.array([[3, 1], [2, 2]]))

    def test_the_label_order_of_the_contract_is_kept(self) -> None:
        self.assertEqual(self.result.labels, LABELS)

    def test_a_label_the_run_never_predicted_still_has_its_row_and_column(self) -> None:
        result = evaluate_split(
            build_part(TEST_SPLIT, TARGETS),
            np.array(["pass"] * TARGETS.size),
        )

        self.assertEqual(result.confusion_matrix.shape, (len(LABELS), len(LABELS)))


class ScoredSplitTest(unittest.TestCase):
    def test_the_result_is_named_after_the_split_it_scored(self) -> None:
        result = evaluate_split(build_part(VALIDATION_SPLIT, TARGETS), PREDICTIONS)

        self.assertEqual(result.split_name, VALIDATION_SPLIT)

    def test_predictions_that_do_not_match_the_split_are_rejected(self) -> None:
        with self.assertRaises(EvaluationError) as raised:
            evaluate_split(build_part(TEST_SPLIT, TARGETS), PREDICTIONS[:4])

        self.assertIn("8 rows", str(raised.exception))
        self.assertIn("4 predictions", str(raised.exception))


class EvaluateModelTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = CountingPipeline(PREDICTIONS)
        self.model = TrainedModel(
            report=build_report(),
            split=DataSplit(
                train=build_part("train", TARGETS),
                validation=build_part(VALIDATION_SPLIT, TARGETS),
                test=build_part(TEST_SPLIT, TARGETS),
            ),
            pipeline=self.pipeline,
            validation_predictions=PREDICTIONS,
        )
        self.evaluation = evaluate_model(self.model)

    def test_the_validation_and_the_test_are_scored_apart(self) -> None:
        self.assertEqual(self.evaluation.validation.split_name, VALIDATION_SPLIT)
        self.assertEqual(self.evaluation.test.split_name, TEST_SPLIT)
        self.assertEqual(
            [result.split_name for result in self.evaluation.results],
            [VALIDATION_SPLIT, TEST_SPLIT],
        )

    def test_the_test_part_is_predicted_exactly_once(self) -> None:
        self.assertEqual(self.pipeline.predicted_rows, [self.model.split.test.row_count])

    def test_the_validation_is_scored_from_the_predictions_of_the_training(self) -> None:
        expected = evaluate_split(self.model.split.validation, self.model.validation_predictions)

        self.assertEqual(self.evaluation.validation.metrics, expected.metrics)


if __name__ == "__main__":
    unittest.main()
