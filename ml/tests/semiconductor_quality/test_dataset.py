from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from ml.semiconductor_quality import dataset as dataset_module
from ml.semiconductor_quality.dataset import (
    MINIMUM_ROWS_PER_LABEL,
    DatasetValidationError,
    load_training_input,
    resolve_csv_path,
)
from ml.semiconductor_quality.domain import (
    CATEGORICAL_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    IDENTIFIER_COLUMN,
    LABELS,
    NUMERIC_FEATURE_COLUMNS,
    REQUIRED_COLUMNS,
    TARGET_COLUMN,
    FetchedDataset,
)


HEADER = ",".join(REQUIRED_COLUMNS)

VALUES_BY_COLUMN: dict[str, str] = {
    IDENTIFIER_COLUMN: "SAMPLE-00001",
    "temperature": "450.10000",
    "pressure": "100.20000",
    "process_time": "60.30000",
    "gas_flow": "50.40000",
    "sensor_1": "0.50000",
    "sensor_2": "0.60000",
    "inspection_value": "10.70000",
    "equipment_id": "EQ-01",
    "process_step": "ETCH",
    TARGET_COLUMN: "pass",
}


def build_line(index: int, **overrides: str) -> str:
    values = {**VALUES_BY_COLUMN, IDENTIFIER_COLUMN: f"SAMPLE-{index:05d}", **overrides}
    return ",".join(values[column] for column in REQUIRED_COLUMNS)


def build_balanced_lines(rows_per_label: int = MINIMUM_ROWS_PER_LABEL) -> list[str]:
    """Build the smallest input that every label check accepts."""
    lines = []
    for index, label in enumerate(LABELS * rows_per_label, start=1):
        lines.append(build_line(index, result=label))
    return lines


class DatasetFileTestCase(unittest.TestCase):
    """Writes a CSV into a throwaway stand-in for the ClearML dataset cache."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def write_csv(self, *lines: str, name: str = "semiconductor_quality.csv") -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def fetched(self) -> FetchedDataset:
        return FetchedDataset(
            dataset_id="dataset-id",
            dataset_project="Semiconductor Quality Prediction",
            dataset_name="semiconductor-quality-data",
            dataset_version="1.0.0",
            local_root=self.root,
        )

    def load(self, *lines: str, csv_path: str = "semiconductor_quality.csv"):
        self.write_csv(*lines, name=csv_path)
        return load_training_input(self.fetched(), csv_path)

    def failure(self, *lines: str, csv_path: str = "semiconductor_quality.csv") -> str:
        with self.assertRaises(DatasetValidationError) as raised:
            self.load(*lines, csv_path=csv_path)
        return str(raised.exception)


class DatasetIndependenceTest(unittest.TestCase):
    def test_the_input_validation_does_not_import_the_clearml_sdk(self) -> None:
        source = Path(dataset_module.__file__).read_text(encoding="utf-8")

        self.assertNotIn("import clearml", source)
        self.assertNotIn("from clearml", source)


class ResolveCsvPathTest(DatasetFileTestCase):
    def test_a_relative_path_is_resolved_inside_the_cache_root(self) -> None:
        expected = self.write_csv(HEADER, name="nested/quality.csv")

        resolved = resolve_csv_path(self.root, "nested/quality.csv")

        self.assertEqual(resolved, expected)

    def test_a_missing_file_is_rejected(self) -> None:
        with self.assertRaises(DatasetValidationError) as raised:
            resolve_csv_path(self.root, "semiconductor_quality.csv")

        self.assertIn("was not found", str(raised.exception))

    def test_a_directory_is_not_accepted_as_the_input_file(self) -> None:
        (self.root / "nested").mkdir()

        with self.assertRaises(DatasetValidationError):
            resolve_csv_path(self.root, "nested")

    def test_a_path_that_escapes_the_cache_root_is_rejected(self) -> None:
        outside = self.root.parent / "outside.csv"
        outside.write_text(HEADER + "\n", encoding="utf-8")
        self.addCleanup(outside.unlink)

        with self.assertRaises(DatasetValidationError) as raised:
            resolve_csv_path(self.root, "../outside.csv")

        self.assertIn("points outside", str(raised.exception))
        self.assertTrue(outside.is_file())

    def test_an_absolute_path_is_rejected(self) -> None:
        with self.assertRaises(DatasetValidationError) as raised:
            resolve_csv_path(self.root, "/etc/hostname")

        self.assertIn("points outside", str(raised.exception))

    def test_a_soft_linked_file_of_the_cache_is_accepted(self) -> None:
        """ClearML builds the local copy out of soft links on POSIX systems."""
        stored = self.root.parent / "chunk.csv"
        stored.write_text(HEADER + "\n", encoding="utf-8")
        self.addCleanup(stored.unlink)
        link = self.root / "semiconductor_quality.csv"
        link.symlink_to(stored)

        self.assertEqual(resolve_csv_path(self.root, "semiconductor_quality.csv"), link)


class ValidInputTest(DatasetFileTestCase):
    def test_the_resolved_dataset_identity_is_kept_in_the_report(self) -> None:
        report = self.load(HEADER, *build_balanced_lines()).report

        self.assertEqual(report.source.dataset_id, "dataset-id")
        self.assertEqual(report.source.dataset_version, "1.0.0")
        self.assertEqual(report.source.dataset_name, "semiconductor-quality-data")
        self.assertEqual(report.source.csv_path, self.root / "semiconductor_quality.csv")

    def test_the_row_count_and_label_distribution_are_reported(self) -> None:
        report = self.load(HEADER, *build_balanced_lines(rows_per_label=4)).report

        self.assertEqual(report.row_count, 8)
        self.assertEqual(dict(report.label_counts), {"pass": 4, "fail": 4})

    def test_the_identifier_and_the_target_are_not_features(self) -> None:
        report = self.load(HEADER, *build_balanced_lines()).report

        self.assertEqual(report.feature_names, FEATURE_COLUMNS)
        self.assertNotIn(IDENTIFIER_COLUMN, report.feature_names)
        self.assertNotIn(TARGET_COLUMN, report.feature_names)

    def test_numeric_and_categorical_features_are_reported_separately(self) -> None:
        report = self.load(HEADER, *build_balanced_lines()).report

        self.assertEqual(report.numeric_feature_names, NUMERIC_FEATURE_COLUMNS)
        self.assertEqual(report.categorical_feature_names, CATEGORICAL_FEATURE_COLUMNS)
        self.assertEqual(
            report.numeric_feature_names + report.categorical_feature_names,
            report.feature_names,
        )

    def test_the_features_keep_the_column_order_of_the_contract(self) -> None:
        training_input = self.load(
            HEADER,
            build_line(1, temperature="1.5", equipment_id="EQ-02", result="pass"),
            build_line(2, result="pass"),
            build_line(3, result="pass"),
            *(build_line(index, result="fail") for index in range(4, 7)),
        )

        self.assertEqual(training_input.features.shape, (6, len(FEATURE_COLUMNS)))
        self.assertEqual(training_input.features[0][0], 1.5)
        self.assertEqual(
            training_input.features[0][len(NUMERIC_FEATURE_COLUMNS)],
            "EQ-02",
        )

    def test_numeric_features_are_read_as_finite_numbers(self) -> None:
        training_input = self.load(HEADER, *build_balanced_lines())

        numeric = training_input.features[:, : len(NUMERIC_FEATURE_COLUMNS)].astype(float)
        self.assertTrue(np.isfinite(numeric).all())

    def test_the_targets_follow_the_row_order_of_the_file(self) -> None:
        training_input = self.load(HEADER, *build_balanced_lines())

        self.assertEqual(
            list(training_input.targets),
            ["pass", "fail"] * MINIMUM_ROWS_PER_LABEL,
        )
        self.assertEqual(training_input.targets.shape[0], training_input.features.shape[0])

    def test_surrounding_whitespace_is_not_part_of_a_value(self) -> None:
        training_input = self.load(
            HEADER,
            build_line(1, temperature=" 1.5 ", equipment_id=" EQ-02 ", result="pass"),
            *(build_line(index, result="pass") for index in range(2, 4)),
            *(build_line(index, result="fail") for index in range(4, 7)),
        )

        self.assertEqual(training_input.features[0][0], 1.5)
        self.assertEqual(training_input.features[0][len(NUMERIC_FEATURE_COLUMNS)], "EQ-02")

    def test_columns_beyond_the_contract_are_ignored(self) -> None:
        header = HEADER + ",operator_note"
        lines = [f"{line},checked" for line in build_balanced_lines()]

        report = self.load(header, *lines).report

        self.assertEqual(report.feature_names, FEATURE_COLUMNS)
        self.assertEqual(report.row_count, len(LABELS) * MINIMUM_ROWS_PER_LABEL)


class SchemaValidationTest(DatasetFileTestCase):
    def test_a_missing_required_column_is_named(self) -> None:
        kept = [column for column in REQUIRED_COLUMNS if column != "sensor_2"]
        header = ",".join(kept)
        lines = [
            ",".join({**VALUES_BY_COLUMN, TARGET_COLUMN: label}[column] for column in kept)
            for label in LABELS * MINIMUM_ROWS_PER_LABEL
        ]

        message = self.failure(header, *lines)

        self.assertIn("required columns are missing", message)
        self.assertIn("sensor_2", message)

    def test_a_duplicated_column_is_rejected(self) -> None:
        header = HEADER + f",{TARGET_COLUMN}"
        lines = [f"{line},fail" for line in build_balanced_lines()]

        message = self.failure(header, *lines)

        self.assertIn("declared more than once", message)
        self.assertIn(TARGET_COLUMN, message)

    def test_an_empty_file_is_rejected(self) -> None:
        path = self.root / "semiconductor_quality.csv"
        path.write_text("", encoding="utf-8")

        with self.assertRaises(DatasetValidationError) as raised:
            load_training_input(self.fetched(), "semiconductor_quality.csv")

        self.assertIn("no header", str(raised.exception))

    def test_a_file_without_data_rows_is_rejected(self) -> None:
        message = self.failure(HEADER)

        self.assertIn("no data rows", message)

    def test_a_byte_order_mark_does_not_hide_the_first_column(self) -> None:
        path = self.root / "semiconductor_quality.csv"
        path.write_text(
            "\n".join([HEADER, *build_balanced_lines()]) + "\n",
            encoding="utf-8-sig",
        )

        report = load_training_input(self.fetched(), "semiconductor_quality.csv").report

        self.assertEqual(report.row_count, len(LABELS) * MINIMUM_ROWS_PER_LABEL)

    def test_the_failure_names_the_dataset_version_and_file(self) -> None:
        message = self.failure(HEADER)

        self.assertIn("1.0.0", message)
        self.assertIn("dataset-id", message)
        self.assertIn("semiconductor_quality.csv", message)


class ValueValidationTest(DatasetFileTestCase):
    def test_a_missing_value_is_reported_with_its_line(self) -> None:
        message = self.failure(HEADER, *build_balanced_lines(), build_line(7, pressure=""))

        self.assertIn("line 8: pressure is empty", message)

    def test_a_line_with_too_few_values_is_reported(self) -> None:
        short = ",".join(VALUES_BY_COLUMN[column] for column in REQUIRED_COLUMNS[:-1])

        message = self.failure(HEADER, *build_balanced_lines(), short)

        self.assertIn(f"line 8: {TARGET_COLUMN} is missing", message)

    def test_a_line_with_too_many_values_is_reported(self) -> None:
        message = self.failure(HEADER, *build_balanced_lines(), build_line(7) + ",surplus")

        self.assertIn("line 8 holds more values than the header declares", message)

    def test_a_non_numeric_measurement_is_rejected(self) -> None:
        message = self.failure(HEADER, *build_balanced_lines(), build_line(7, temperature="warm"))

        self.assertIn("line 8: temperature is not a number", message)

    def test_an_infinite_measurement_is_rejected(self) -> None:
        message = self.failure(HEADER, *build_balanced_lines(), build_line(7, gas_flow="inf"))

        self.assertIn("line 8: gas_flow must be a finite number", message)

    def test_a_missing_measurement_written_as_nan_is_rejected(self) -> None:
        message = self.failure(HEADER, *build_balanced_lines(), build_line(7, sensor_1="NaN"))

        self.assertIn("line 8: sensor_1 must be a finite number", message)

    def test_every_broken_column_of_a_line_is_reported_at_once(self) -> None:
        message = self.failure(
            HEADER,
            *build_balanced_lines(),
            build_line(7, temperature="warm", equipment_id=""),
        )

        self.assertIn("temperature is not a number", message)
        self.assertIn("equipment_id is empty", message)

    def test_a_long_run_of_broken_lines_is_summarised(self) -> None:
        broken = [build_line(index, pressure="") for index in range(7, 20)]

        message = self.failure(HEADER, *build_balanced_lines(), *broken)

        self.assertIn("more invalid values", message)
        self.assertLessEqual(message.count("pressure is empty"), 5)


class LabelValidationTest(DatasetFileTestCase):
    def test_an_unknown_label_is_rejected(self) -> None:
        message = self.failure(HEADER, *build_balanced_lines(), build_line(7, result="unknown"))

        self.assertIn(f"line 8: {TARGET_COLUMN} must be one of pass, fail", message)

    def test_a_label_that_cannot_be_split_is_rejected(self) -> None:
        lines = [build_line(index, result="pass") for index in range(1, 6)]
        lines.append(build_line(6, result="fail"))

        message = self.failure(HEADER, *lines)

        self.assertIn(f"must hold at least {MINIMUM_ROWS_PER_LABEL} rows of 'fail'", message)

    def test_a_single_class_input_is_rejected(self) -> None:
        lines = [build_line(index, result="pass") for index in range(1, 10)]

        message = self.failure(HEADER, *lines)

        self.assertIn("'fail'", message)

    def test_a_duplicated_sample_id_is_rejected(self) -> None:
        lines = [*build_balanced_lines(), build_line(1, result="fail")]

        message = self.failure(HEADER, *lines)

        self.assertIn(f"{IDENTIFIER_COLUMN} must be unique", message)
        self.assertIn("SAMPLE-00001", message)


if __name__ == "__main__":
    unittest.main()
