from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

import numpy as np

from ml.semiconductor_quality import config, domain
from ml.semiconductor_quality.domain import (
    IDENTIFIER_COLUMN,
    LABELS,
    POSITIVE_LABEL,
    TARGET_COLUMN,
    DataSplit,
    DatasetSource,
    DatasetValidationReport,
    EvaluationResult,
    SplitPart,
    TrainingInput,
)


def build_source() -> DatasetSource:
    return DatasetSource(
        dataset_id="d1",
        dataset_project="Semiconductor Quality Prediction",
        dataset_name="semiconductor-quality-data",
        dataset_version="1.0.0",
        csv_path=Path("/cache/semiconductor_quality.csv"),
    )


def build_part(name: str, row_count: int) -> SplitPart:
    return SplitPart(
        name=name,
        features=np.zeros((row_count, 2)),
        targets=np.array(["pass"] * row_count),
        label_counts={"pass": row_count, "fail": 0},
    )


class DomainIndependenceTest(unittest.TestCase):
    def test_data_contracts_do_not_import_the_clearml_sdk(self) -> None:
        for module in (domain, config):
            with self.subTest(module=module.__name__):
                source = Path(module.__file__).read_text(encoding="utf-8")

                self.assertNotIn("import clearml", source)
                self.assertNotIn("from clearml", source)


class DomainContractTest(unittest.TestCase):
    def test_label_contract_matches_the_upstream_dataset(self) -> None:
        self.assertEqual(IDENTIFIER_COLUMN, "sample_id")
        self.assertEqual(TARGET_COLUMN, "result")
        self.assertEqual(LABELS, ("pass", "fail"))
        self.assertIn(POSITIVE_LABEL, LABELS)

    def test_contracts_are_immutable(self) -> None:
        contracts = (
            DatasetSource,
            DatasetValidationReport,
            TrainingInput,
            SplitPart,
            DataSplit,
            EvaluationResult,
        )
        for contract in contracts:
            with self.subTest(contract=contract.__name__):
                self.assertTrue(dataclasses.fields(contract))
                self.assertTrue(contract.__dataclass_params__.frozen)

    def test_split_part_reports_its_row_count(self) -> None:
        part = build_part("train", 12)

        self.assertEqual(part.row_count, 12)

    def test_split_exposes_its_three_mutually_exclusive_parts(self) -> None:
        split = DataSplit(
            train=build_part("train", 6),
            validation=build_part("validation", 2),
            test=build_part("test", 2),
        )

        self.assertEqual([part.name for part in split.parts], ["train", "validation", "test"])

    def test_validation_report_keeps_the_resolved_dataset_identity(self) -> None:
        report = DatasetValidationReport(
            source=build_source(),
            row_count=3,
            feature_names=("temperature", "equipment_id"),
            numeric_feature_names=("temperature",),
            categorical_feature_names=("equipment_id",),
            label_counts={"pass": 2, "fail": 1},
        )

        self.assertEqual(report.source.dataset_id, "d1")
        self.assertEqual(report.source.dataset_version, "1.0.0")
        self.assertNotIn(TARGET_COLUMN, report.feature_names)
        self.assertNotIn(IDENTIFIER_COLUMN, report.feature_names)

    def test_evaluation_result_defaults_to_the_shared_label_order(self) -> None:
        result = EvaluationResult(
            split_name="test",
            metrics={"accuracy": 1.0},
            confusion_matrix=np.array([[2, 0], [0, 1]]),
        )

        self.assertEqual(result.labels, LABELS)


if __name__ == "__main__":
    unittest.main()
