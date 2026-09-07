from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from ml.semiconductor_quality import preprocess as preprocess_module
from ml.semiconductor_quality.config import SplitConfig
from ml.semiconductor_quality.domain import (
    CATEGORICAL_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    LABELS,
    NUMERIC_FEATURE_COLUMNS,
    DatasetSource,
    DatasetValidationReport,
    SplitPart,
    TrainingInput,
)
from ml.semiconductor_quality.preprocess import (
    CATEGORICAL_TRANSFORMER,
    NUMERIC_TRANSFORMER,
    PreprocessingError,
    build_preprocessor,
    split_training_input,
)


SEED = 20260906
EQUIPMENT = ("EQ-01", "EQ-02")
PROCESS_STEPS = ("ETCH", "CVD")

# The first numeric column carries the row number, so a row stays identifiable
# after it has been shuffled into one of the three parts.
ROW_NUMBER_COLUMN = 0


def build_report(label_counts: dict[str, int]) -> DatasetValidationReport:
    return DatasetValidationReport(
        source=DatasetSource(
            dataset_id="dataset-id",
            dataset_project="Semiconductor Quality Prediction",
            dataset_name="semiconductor-quality-data",
            dataset_version="1.0.0",
            csv_path=Path("/cache/semiconductor_quality.csv"),
        ),
        row_count=sum(label_counts.values()),
        feature_names=FEATURE_COLUMNS,
        numeric_feature_names=NUMERIC_FEATURE_COLUMNS,
        categorical_feature_names=CATEGORICAL_FEATURE_COLUMNS,
        label_counts=label_counts,
    )


def build_training_input(pass_rows: int, fail_rows: int) -> TrainingInput:
    """Build an input whose rows are told apart by their row number."""
    targets = np.array(["pass"] * pass_rows + ["fail"] * fail_rows)
    features = np.empty((targets.size, len(FEATURE_COLUMNS)), dtype=object)
    for row in range(targets.size):
        numeric = [float(row)] + [float(row % 7) for _ in NUMERIC_FEATURE_COLUMNS[1:]]
        categorical = [
            EQUIPMENT[row % len(EQUIPMENT)],
            PROCESS_STEPS[row % len(PROCESS_STEPS)],
        ]
        features[row] = (*numeric, *categorical)
    return TrainingInput(
        report=build_report({"pass": pass_rows, "fail": fail_rows}),
        features=features,
        targets=targets,
    )


def row_numbers(part: SplitPart) -> list[int]:
    return [int(value) for value in part.features[:, ROW_NUMBER_COLUMN]]


class PreprocessIndependenceTest(unittest.TestCase):
    def test_the_split_and_the_preprocessing_do_not_import_the_clearml_sdk(self) -> None:
        source = Path(preprocess_module.__file__).read_text(encoding="utf-8")

        self.assertNotIn("import clearml", source)
        self.assertNotIn("from clearml", source)


class SplitPartitionTest(unittest.TestCase):
    def test_every_row_ends_up_in_exactly_one_part(self) -> None:
        training_input = build_training_input(pass_rows=60, fail_rows=40)

        split = split_training_input(training_input, SplitConfig(), SEED)

        assigned = [number for part in split.parts for number in row_numbers(part)]
        self.assertEqual(sorted(assigned), list(range(100)))

    def test_the_parts_are_named_after_their_purpose(self) -> None:
        split = split_training_input(build_training_input(60, 40), SplitConfig(), SEED)

        self.assertEqual(
            [part.name for part in split.parts],
            ["train", "validation", "test"],
        )

    def test_the_rows_of_a_part_keep_the_order_of_the_input(self) -> None:
        split = split_training_input(build_training_input(60, 40), SplitConfig(), SEED)

        for part in split.parts:
            with self.subTest(part=part.name):
                self.assertEqual(row_numbers(part), sorted(row_numbers(part)))

    def test_the_features_of_a_part_stay_aligned_with_its_targets(self) -> None:
        training_input = build_training_input(pass_rows=60, fail_rows=40)

        split = split_training_input(training_input, SplitConfig(), SEED)

        for part in split.parts:
            with self.subTest(part=part.name):
                expected = training_input.targets[row_numbers(part)]
                self.assertEqual(list(part.targets), list(expected))


class SplitRatioTest(unittest.TestCase):
    def test_the_row_counts_follow_the_configured_ratios(self) -> None:
        split = split_training_input(build_training_input(60, 40), SplitConfig(), SEED)

        self.assertEqual(
            [part.row_count for part in split.parts],
            [60, 20, 20],
        )

    def test_another_ratio_moves_the_rows_between_the_parts(self) -> None:
        split = split_training_input(
            build_training_input(60, 40),
            SplitConfig(train_ratio=0.5, validation_ratio=0.25, test_ratio=0.25),
            SEED,
        )

        self.assertEqual([part.row_count for part in split.parts], [50, 25, 25])


class SplitStratificationTest(unittest.TestCase):
    def test_every_part_keeps_the_label_ratio_of_the_input(self) -> None:
        split = split_training_input(build_training_input(60, 40), SplitConfig(), SEED)

        self.assertEqual(split.train.label_counts, {"pass": 36, "fail": 24})
        self.assertEqual(split.validation.label_counts, {"pass": 12, "fail": 8})
        self.assertEqual(split.test.label_counts, {"pass": 12, "fail": 8})

    def test_the_reported_label_counts_match_the_rows_of_the_part(self) -> None:
        split = split_training_input(build_training_input(60, 40), SplitConfig(), SEED)

        for part in split.parts:
            with self.subTest(part=part.name):
                counted = {label: list(part.targets).count(label) for label in LABELS}
                self.assertEqual(dict(part.label_counts), counted)

    def test_a_rare_label_stays_present_in_every_part(self) -> None:
        split = split_training_input(build_training_input(200, 4), SplitConfig(), SEED)

        for part in split.parts:
            with self.subTest(part=part.name):
                self.assertGreaterEqual(part.label_counts["fail"], 1)

    def test_the_smallest_accepted_input_still_fills_every_part(self) -> None:
        split = split_training_input(build_training_input(3, 3), SplitConfig(), SEED)

        for part in split.parts:
            with self.subTest(part=part.name):
                self.assertEqual(dict(part.label_counts), {"pass": 1, "fail": 1})

    def test_a_label_that_cannot_fill_every_part_is_rejected(self) -> None:
        with self.assertRaises(PreprocessingError) as raised:
            split_training_input(build_training_input(60, 2), SplitConfig(), SEED)

        self.assertIn("'fail'", str(raised.exception))
        self.assertIn("2 rows", str(raised.exception))


class SplitReproducibilityTest(unittest.TestCase):
    def test_the_same_seed_repeats_the_split(self) -> None:
        training_input = build_training_input(pass_rows=60, fail_rows=40)

        first = split_training_input(training_input, SplitConfig(), SEED)
        second = split_training_input(training_input, SplitConfig(), SEED)

        for left, right in zip(first.parts, second.parts):
            with self.subTest(part=left.name):
                self.assertEqual(row_numbers(left), row_numbers(right))

    def test_another_seed_draws_other_rows(self) -> None:
        training_input = build_training_input(pass_rows=60, fail_rows=40)

        first = split_training_input(training_input, SplitConfig(), SEED)
        second = split_training_input(training_input, SplitConfig(), SEED + 1)

        self.assertNotEqual(row_numbers(first.test), row_numbers(second.test))


class PreprocessorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.training_input = build_training_input(pass_rows=60, fail_rows=40)
        self.report = self.training_input.report

    def test_the_columns_are_addressed_by_their_place_in_the_feature_contract(self) -> None:
        transformers = {
            name: columns for name, _, columns in build_preprocessor(self.report).transformers
        }

        self.assertEqual(transformers[NUMERIC_TRANSFORMER], list(range(7)))
        self.assertEqual(transformers[CATEGORICAL_TRANSFORMER], [7, 8])

    def test_the_transformed_matrix_is_numeric(self) -> None:
        preprocessor = build_preprocessor(self.report)

        transformed = preprocessor.fit_transform(self.training_input.features)

        self.assertEqual(transformed.dtype, np.float64)
        self.assertEqual(transformed.shape[0], self.training_input.features.shape[0])

    def test_every_category_becomes_its_own_column(self) -> None:
        preprocessor = build_preprocessor(self.report)

        transformed = preprocessor.fit_transform(self.training_input.features)

        expected = len(NUMERIC_FEATURE_COLUMNS) + len(EQUIPMENT) + len(PROCESS_STEPS)
        self.assertEqual(transformed.shape[1], expected)

    def test_a_category_that_was_not_fitted_does_not_break_the_transform(self) -> None:
        preprocessor = build_preprocessor(self.report)
        preprocessor.fit(self.training_input.features)
        unseen = self.training_input.features[:1].copy()
        unseen[0, len(NUMERIC_FEATURE_COLUMNS)] = "EQ-99"

        transformed = preprocessor.transform(unseen)

        equipment_columns = transformed[0, len(NUMERIC_FEATURE_COLUMNS) : -len(PROCESS_STEPS)]
        self.assertEqual(list(equipment_columns), [0.0] * len(EQUIPMENT))

    def test_a_column_the_input_does_not_hold_is_rejected(self) -> None:
        report = build_report({"pass": 1, "fail": 1})
        without_categories = DatasetValidationReport(
            source=report.source,
            row_count=report.row_count,
            feature_names=NUMERIC_FEATURE_COLUMNS,
            numeric_feature_names=NUMERIC_FEATURE_COLUMNS,
            categorical_feature_names=CATEGORICAL_FEATURE_COLUMNS,
            label_counts=report.label_counts,
        )

        with self.assertRaises(PreprocessingError) as raised:
            build_preprocessor(without_categories)

        self.assertIn("equipment_id", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
