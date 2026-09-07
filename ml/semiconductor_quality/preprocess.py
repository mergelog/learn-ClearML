"""Split the validated input and build the preprocessing of the pipeline.

This module never contacts ClearML. It receives the learning input that
:mod:`dataset` validated and produces the two things a fit needs: three
mutually exclusive parts, and the column wise preprocessing that turns the
feature matrix into numbers.

The split is stratified on the target and driven by a single seed, so the same
Dataset version and the same configuration always yield the same three parts.
The rows are allocated per label rather than by chaining two
``train_test_split`` calls: a three way stratified split of a small label
leaves a single row for the second call, which cannot be stratified any more.
Allocating each label directly keeps the smallest Dataset the input validation
accepts splittable, and keeps every part non empty.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import SplitConfig
from .domain import (
    LABELS,
    TEST_SPLIT,
    TRAIN_SPLIT,
    VALIDATION_SPLIT,
    DataSplit,
    DatasetValidationReport,
    SplitPart,
    TrainingInput,
)


SPLIT_NAMES = (TRAIN_SPLIT, VALIDATION_SPLIT, TEST_SPLIT)

NUMERIC_TRANSFORMER = "numeric"
CATEGORICAL_TRANSFORMER = "categorical"


class PreprocessingError(ValueError):
    """Raised when the validated input cannot be prepared for a fit."""


def split_training_input(
    training_input: TrainingInput,
    split: SplitConfig,
    random_seed: int,
) -> DataSplit:
    """Split the rows into stratified train / validation / test parts.

    Every row ends up in exactly one part, and every label is represented in
    all three, so the validation and the final evaluation stay comparable to
    the data the model was fitted on.
    """
    generator = np.random.default_rng(random_seed)
    rows_by_split: dict[str, list[int]] = {name: [] for name in SPLIT_NAMES}

    for label in LABELS:
        rows = np.flatnonzero(training_input.targets == label)
        shuffled = rows[generator.permutation(rows.size)]
        offset = 0
        for name, count in zip(SPLIT_NAMES, _allocate(label, int(rows.size), split)):
            rows_by_split[name].extend(int(row) for row in shuffled[offset : offset + count])
            offset += count

    return DataSplit(
        train=_build_part(TRAIN_SPLIT, training_input, rows_by_split[TRAIN_SPLIT]),
        validation=_build_part(VALIDATION_SPLIT, training_input, rows_by_split[VALIDATION_SPLIT]),
        test=_build_part(TEST_SPLIT, training_input, rows_by_split[TEST_SPLIT]),
    )


def build_preprocessor(report: DatasetValidationReport) -> ColumnTransformer:
    """Build the column wise preprocessing of the fitted pipeline.

    The columns are addressed by their position in the feature contract, which
    is also the layout :mod:`dataset` builds, so an upstream column order does
    not change what a fitted model expects.

    A forest does not need the numeric columns scaled. Scaling them is kept
    anyway because it states the numeric block explicitly, and because it is
    fitted on the training rows only, which is where a leak into the
    validation and test parts would otherwise start.
    """
    return ColumnTransformer(
        transformers=[
            (
                NUMERIC_TRANSFORMER,
                StandardScaler(),
                _column_indices(report, report.numeric_feature_names),
            ),
            (
                CATEGORICAL_TRANSFORMER,
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                _column_indices(report, report.categorical_feature_names),
            ),
        ]
    )


def _allocate(label: str, row_count: int, split: SplitConfig) -> tuple[int, int, int]:
    """Divide the rows of one label over the three parts.

    The ratios are honoured by the largest remainder method, and every part is
    then guaranteed at least one row, so a rare label stays present everywhere
    instead of disappearing from the smallest part.
    """
    if row_count < len(SPLIT_NAMES):
        raise PreprocessingError(
            f"label {label!r} holds {row_count} rows, which cannot fill "
            f"{', '.join(SPLIT_NAMES)} without leaving a part empty"
        )

    exact = [row_count * ratio for ratio in _ratios(split)]
    counts = [math.floor(value) for value in exact]
    remainders = sorted(range(len(counts)), key=lambda index: -(exact[index] - counts[index]))
    for index in remainders[: row_count - sum(counts)]:
        counts[index] += 1

    for index, count in enumerate(counts):
        if count == 0:
            donor = max(range(len(counts)), key=lambda candidate: counts[candidate])
            counts[donor] -= 1
            counts[index] += 1

    return counts[0], counts[1], counts[2]


def _ratios(split: SplitConfig) -> tuple[float, float, float]:
    return split.train_ratio, split.validation_ratio, split.test_ratio


def _build_part(name: str, training_input: TrainingInput, rows: Sequence[int]) -> SplitPart:
    # The rows of a part are kept in the order of the input file, so a part is
    # not laid out label by label and stays comparable to the source CSV.
    ordered = np.array(sorted(rows), dtype=int)
    targets = training_input.targets[ordered]
    return SplitPart(
        name=name,
        features=training_input.features[ordered],
        targets=targets,
        label_counts=_count_labels(targets),
    )


def _count_labels(targets: np.ndarray) -> Mapping[str, int]:
    counts = Counter(str(target) for target in targets)
    return {label: counts[label] for label in LABELS}


def _column_indices(
    report: DatasetValidationReport,
    columns: Sequence[str],
) -> list[int]:
    missing = [column for column in columns if column not in report.feature_names]
    if missing:
        raise PreprocessingError(
            f"the validated input does not hold the columns to preprocess: {', '.join(missing)}"
        )
    return [report.feature_names.index(column) for column in columns]
