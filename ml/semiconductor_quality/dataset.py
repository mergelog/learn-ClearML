"""Turn the fetched ClearML Dataset into a validated learning input.

This module never contacts ClearML. It receives the read-only local copy that
:mod:`clearml_tracking` downloaded, resolves the requested CSV inside it, and
either produces a :class:`~.domain.TrainingInput` or refuses the run.

Validation happens before any model is fitted, so a broken upstream Dataset
version fails with the offending columns and lines named, instead of failing
later inside scikit-learn or, worse, training on silently wrong values.
"""

from __future__ import annotations

import csv
import math
import os
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .domain import (
    CATEGORICAL_FEATURE_COLUMNS,
    FEATURE_COLUMNS,
    IDENTIFIER_COLUMN,
    LABELS,
    NUMERIC_FEATURE_COLUMNS,
    REQUIRED_COLUMNS,
    TARGET_COLUMN,
    DatasetSource,
    DatasetValidationReport,
    FetchedDataset,
    TrainingInput,
)


# A stratified split into three mutually exclusive parts needs at least one row
# per label in every part, so a label below this count cannot be learned from.
MINIMUM_ROWS_PER_LABEL = 3

# Reporting every broken line of a large Dataset would bury the first cause.
MAXIMUM_REPORTED_ITEMS = 5

# ``csv.DictReader`` collects the values a line has beyond its header under this
# key, which is how a line with too many columns is detected.
SURPLUS_VALUES_KEY = None


class DatasetValidationError(ValueError):
    """Raised when the fetched Dataset cannot be used as a learning input."""


def load_training_input(fetched: FetchedDataset, csv_path: str) -> TrainingInput:
    """Read one CSV of the fetched Dataset version as a validated learning input."""
    source = DatasetSource(
        dataset_id=fetched.dataset_id,
        dataset_project=fetched.dataset_project,
        dataset_name=fetched.dataset_name,
        dataset_version=fetched.dataset_version,
        csv_path=resolve_csv_path(fetched.local_root, csv_path),
    )
    return read_training_input(source)


def resolve_csv_path(dataset_root: Path | str, csv_path: str) -> Path:
    """Join a Dataset relative path onto the cache root without escaping it.

    The join is normalised lexically rather than through :meth:`Path.resolve`,
    because ClearML builds the local copy out of soft links on POSIX systems:
    resolving them would point every legitimate file outside the cache root.
    """
    root = Path(dataset_root).resolve()
    candidate = Path(os.path.normpath(root / csv_path))
    if not candidate.is_relative_to(root):
        raise DatasetValidationError(
            f"{csv_path!r} points outside the fetched dataset root {root}"
        )
    if not candidate.is_file():
        raise DatasetValidationError(
            f"{csv_path!r} was not found in the fetched dataset root {root}"
        )
    return candidate


def read_training_input(source: DatasetSource) -> TrainingInput:
    """Validate the CSV of a resolved Dataset version and build the learning input."""
    # ``utf-8-sig`` keeps a byte order mark out of the first column name, which
    # would otherwise surface as a missing identifier column.
    with source.csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        _require_schema(source, reader.fieldnames)
        rows = list(reader)
    return _build_training_input(source, rows)


@dataclass(frozen=True)
class _Row:
    """One CSV line that passed validation, in the feature order of the contract."""

    identifier: str
    feature_values: tuple[object, ...]
    target: str


def _require_schema(source: DatasetSource, field_names: Sequence[str] | None) -> None:
    if not field_names:
        raise _invalid_input(source, ("the file is empty, so it has no header",))

    columns = [name.strip() for name in field_names if name is not None]
    duplicates = _repeated(columns)
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]

    errors: list[str] = []
    if missing:
        errors.append(f"required columns are missing: {', '.join(missing)}")
    if duplicates:
        errors.append(f"columns are declared more than once: {', '.join(duplicates)}")
    if errors:
        raise _invalid_input(source, tuple(errors))


def _build_training_input(
    source: DatasetSource,
    rows: Sequence[Mapping[str, str]],
) -> TrainingInput:
    if not rows:
        raise _invalid_input(source, ("the file has a header but no data rows",))

    parsed: list[_Row] = []
    row_errors: list[str] = []
    for line, row in enumerate(rows, start=2):  # line 1 holds the header
        one_row, errors = _parse_row(row, line)
        if one_row is None:
            row_errors.extend(errors)
        else:
            parsed.append(one_row)

    label_counts = Counter(row.target for row in parsed)
    errors = (
        *_summarise(row_errors),
        *_collect_identifier_errors(parsed),
        *_collect_label_errors(label_counts),
    )
    if errors:
        raise _invalid_input(source, errors)

    report = DatasetValidationReport(
        source=source,
        row_count=len(parsed),
        feature_names=FEATURE_COLUMNS,
        numeric_feature_names=NUMERIC_FEATURE_COLUMNS,
        categorical_feature_names=CATEGORICAL_FEATURE_COLUMNS,
        label_counts={label: label_counts[label] for label in LABELS},
    )
    return TrainingInput(
        report=report,
        features=_build_features(parsed),
        targets=np.array([row.target for row in parsed]),
    )


def _parse_row(row: Mapping[str, str], line: int) -> tuple[_Row | None, tuple[str, ...]]:
    """Read one line, or explain every reason why it cannot be learned from."""
    errors: list[str] = []
    if SURPLUS_VALUES_KEY in row:
        errors.append(f"line {line} holds more values than the header declares")

    identifier = _read_text(row, IDENTIFIER_COLUMN, line, errors)
    numeric = [_read_number(row, column, line, errors) for column in NUMERIC_FEATURE_COLUMNS]
    categorical = [
        _read_text(row, column, line, errors) for column in CATEGORICAL_FEATURE_COLUMNS
    ]
    target = _read_label(row, line, errors)

    if errors:
        return None, tuple(errors)
    return _Row(identifier=identifier, feature_values=(*numeric, *categorical), target=target), ()


def _read_text(row: Mapping[str, str], column: str, line: int, errors: list[str]) -> str:
    value = row.get(column)
    if value is None:
        errors.append(f"line {line}: {column} is missing")
        return ""
    text = value.strip()
    if not text:
        errors.append(f"line {line}: {column} is empty")
    return text


def _read_number(row: Mapping[str, str], column: str, line: int, errors: list[str]) -> float:
    before = len(errors)
    text = _read_text(row, column, line, errors)
    if len(errors) != before:
        return math.nan

    try:
        number = float(text)
    except ValueError:
        errors.append(f"line {line}: {column} is not a number, but was {text!r}")
        return math.nan
    if not math.isfinite(number):
        errors.append(f"line {line}: {column} must be a finite number, but was {text!r}")
        return math.nan
    return number


def _read_label(row: Mapping[str, str], line: int, errors: list[str]) -> str:
    before = len(errors)
    text = _read_text(row, TARGET_COLUMN, line, errors)
    if len(errors) != before:
        return ""

    if text not in LABELS:
        errors.append(
            f"line {line}: {TARGET_COLUMN} must be one of {', '.join(LABELS)}, "
            f"but was {text!r}"
        )
    return text


def _build_features(rows: Sequence[_Row]) -> np.ndarray:
    """Lay the features out as one object matrix of floats and category labels.

    ``sample_id`` identifies a row and ``result`` is the answer, so neither is
    part of the matrix a model is allowed to see.
    """
    features = np.empty((len(rows), len(FEATURE_COLUMNS)), dtype=object)
    for index, row in enumerate(rows):
        features[index] = row.feature_values
    return features


def _collect_identifier_errors(rows: Sequence[_Row]) -> tuple[str, ...]:
    duplicates = _repeated([row.identifier for row in rows])
    if not duplicates:
        return ()
    return (
        f"{IDENTIFIER_COLUMN} must be unique, but {_listed(duplicates)} "
        f"occur more than once",
    )


def _collect_label_errors(label_counts: Mapping[str, int]) -> tuple[str, ...]:
    return tuple(
        f"{TARGET_COLUMN} must hold at least {MINIMUM_ROWS_PER_LABEL} rows of "
        f"{label!r} to stay splittable, but it holds {label_counts.get(label, 0)}"
        for label in LABELS
        if label_counts.get(label, 0) < MINIMUM_ROWS_PER_LABEL
    )


def _repeated(values: Sequence[str]) -> tuple[str, ...]:
    counts = Counter(values)
    return tuple(sorted(value for value, count in counts.items() if count > 1))


def _summarise(errors: Sequence[str]) -> tuple[str, ...]:
    if len(errors) <= MAXIMUM_REPORTED_ITEMS:
        return tuple(errors)
    remaining = len(errors) - MAXIMUM_REPORTED_ITEMS
    return (
        *errors[:MAXIMUM_REPORTED_ITEMS],
        f"and {remaining} more invalid values",
    )


def _listed(values: Sequence[str]) -> str:
    shown = ", ".join(values[:MAXIMUM_REPORTED_ITEMS])
    if len(values) <= MAXIMUM_REPORTED_ITEMS:
        return shown
    return f"{shown} and {len(values) - MAXIMUM_REPORTED_ITEMS} more"


def _invalid_input(source: DatasetSource, errors: Sequence[str]) -> DatasetValidationError:
    return DatasetValidationError(
        f"Invalid training input in {source.csv_path} "
        f"(dataset {source.dataset_name} {source.dataset_version}, "
        f"id {source.dataset_id}):\n"
        + "\n".join(f"- {message}" for message in errors)
    )
