"""Data contracts shared by the training flow.

This module intentionally depends on nothing but the standard library and numpy.
Keeping it free of the ClearML SDK lets the data preparation, training and
evaluation steps be exercised without a running ClearML Server.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np


IDENTIFIER_COLUMN = "sample_id"
TARGET_COLUMN = "result"
LABELS = ("pass", "fail")
POSITIVE_LABEL = "fail"

NUMERIC_FEATURE_COLUMNS = (
    "temperature",
    "pressure",
    "process_time",
    "gas_flow",
    "sensor_1",
    "sensor_2",
    "inspection_value",
)
CATEGORICAL_FEATURE_COLUMNS = (
    "equipment_id",
    "process_step",
)

# Numeric columns come first so that a fitted pipeline keeps addressing the
# same feature by the same column index.
FEATURE_COLUMNS = NUMERIC_FEATURE_COLUMNS + CATEGORICAL_FEATURE_COLUMNS
REQUIRED_COLUMNS = (IDENTIFIER_COLUMN, *FEATURE_COLUMNS, TARGET_COLUMN)

TRAIN_SPLIT = "train"
VALIDATION_SPLIT = "validation"
TEST_SPLIT = "test"


@dataclass(frozen=True)
class FetchedDataset:
    """A registered ClearML Dataset version, materialised in the local cache.

    ``local_root`` is the read-only copy that ClearML built for this version.
    It is the only place a training run is allowed to read its input from.
    """

    dataset_id: str
    dataset_project: str
    dataset_name: str
    dataset_version: str
    local_root: Path


@dataclass(frozen=True)
class DatasetSource:
    """Identity of the ClearML Dataset version that an execution actually resolved."""

    dataset_id: str
    dataset_project: str
    dataset_name: str
    dataset_version: str
    csv_path: Path


@dataclass(frozen=True)
class DatasetValidationReport:
    """Outcome of validating the CSV that was fetched from the ClearML Dataset."""

    source: DatasetSource
    row_count: int
    feature_names: tuple[str, ...]
    numeric_feature_names: tuple[str, ...]
    categorical_feature_names: tuple[str, ...]
    label_counts: Mapping[str, int]


@dataclass(frozen=True)
class TrainingInput:
    """Validated learning input, with the identifier and target columns removed."""

    report: DatasetValidationReport
    features: np.ndarray
    targets: np.ndarray


@dataclass(frozen=True)
class SplitPart:
    """One mutually exclusive part of the stratified train / validation / test split."""

    name: str
    features: np.ndarray
    targets: np.ndarray
    label_counts: Mapping[str, int]

    @property
    def row_count(self) -> int:
        return int(self.targets.shape[0])


@dataclass(frozen=True)
class DataSplit:
    train: SplitPart
    validation: SplitPart
    test: SplitPart

    @property
    def parts(self) -> tuple[SplitPart, ...]:
        return (self.train, self.validation, self.test)


@dataclass(frozen=True)
class EvaluationResult:
    """Metrics of a single split, reported under its own ClearML metric series."""

    split_name: str
    metrics: Mapping[str, float]
    confusion_matrix: np.ndarray
    labels: tuple[str, ...] = LABELS


@dataclass(frozen=True)
class TrainingEvaluation:
    """Every split a run is allowed to score, kept apart from one another.

    ``validation`` confirmed the settings of the run and ``test`` is the single
    final evaluation, so the two are never merged into one figure.
    """

    validation: EvaluationResult
    test: EvaluationResult

    @property
    def results(self) -> tuple[EvaluationResult, ...]:
        return (self.validation, self.test)
