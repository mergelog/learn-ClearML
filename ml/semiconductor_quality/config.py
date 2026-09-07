"""Execution contract of the training command.

Two kinds of settings live here and are deliberately kept apart.

``ClearmlSettings`` carries connection endpoints and credentials. It is read
from the environment only, never hard-coded, and never tracked as a ClearML
Task Parameter.

``TrainingConfig`` carries the reproducible part of an execution: which Dataset
version to learn from, where the Task is created, and how the model is fitted.
Everything it holds is safe to record on the Task.

All validation in this module is offline, so an invalid execution is rejected
before a ClearML Task is created.
"""

from __future__ import annotations

import math
import ntpath
import os
from dataclasses import dataclass, field
from pathlib import PurePosixPath


DEFAULT_DATASET_PROJECT = "Semiconductor Quality Prediction"
DEFAULT_DATASET_NAME = "semiconductor-quality-data"
DEFAULT_DATASET_CSV_PATH = "semiconductor_quality.csv"
DEFAULT_DATASET_ALIAS = "training-dataset"

DEFAULT_TASK_PROJECT = f"{DEFAULT_DATASET_PROJECT}/Training"
DEFAULT_TASK_NAME = "random-forest-quality-classifier"

DEFAULT_RANDOM_SEED = 20260906

DEFAULT_API_HOST = "http://localhost:8008"
DEFAULT_WEB_HOST = "http://localhost:8080"
DEFAULT_FILES_HOST = "http://localhost:8081"

RATIO_TOLERANCE = 1e-9


class ConfigurationError(ValueError):
    """Raised when the execution contract is unsatisfiable without contacting ClearML."""


@dataclass(frozen=True)
class DatasetConfig:
    """Which registered ClearML Dataset version the training reads."""

    dataset_version: str
    dataset_project: str = DEFAULT_DATASET_PROJECT
    dataset_name: str = DEFAULT_DATASET_NAME
    dataset_csv_path: str = DEFAULT_DATASET_CSV_PATH
    dataset_alias: str = DEFAULT_DATASET_ALIAS

    def collect_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        errors.extend(_require_text("dataset_version", self.dataset_version))
        errors.extend(_require_text("dataset_project", self.dataset_project))
        errors.extend(_require_text("dataset_name", self.dataset_name))
        errors.extend(_require_text("dataset_alias", self.dataset_alias))
        errors.extend(_require_relative_path("dataset_csv_path", self.dataset_csv_path))
        return tuple(errors)


@dataclass(frozen=True)
class TaskConfig:
    """Where the training Task itself is created, kept separate from the Dataset."""

    task_project: str = DEFAULT_TASK_PROJECT
    task_name: str = DEFAULT_TASK_NAME

    def collect_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        errors.extend(_require_text("task_project", self.task_project))
        errors.extend(_require_text("task_name", self.task_name))
        return tuple(errors)


@dataclass(frozen=True)
class SplitConfig:
    """Ratios of the mutually exclusive train / validation / test split."""

    train_ratio: float = 0.6
    validation_ratio: float = 0.2
    test_ratio: float = 0.2

    @property
    def total_ratio(self) -> float:
        return self.train_ratio + self.validation_ratio + self.test_ratio

    def collect_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        errors.extend(_require_ratio("train_ratio", self.train_ratio))
        errors.extend(_require_ratio("validation_ratio", self.validation_ratio))
        errors.extend(_require_ratio("test_ratio", self.test_ratio))
        if not errors and not math.isclose(self.total_ratio, 1.0, abs_tol=RATIO_TOLERANCE):
            errors.append(
                "train_ratio, validation_ratio and test_ratio must sum to 1.0, "
                f"but they sum to {self.total_ratio}"
            )
        return tuple(errors)


@dataclass(frozen=True)
class RandomForestConfig:
    """RandomForest hyper parameters that a run may vary to create another Task."""

    n_estimators: int = 300
    max_depth: int | None = None
    min_samples_leaf: int = 4

    def collect_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        errors.extend(_require_positive_int("n_estimators", self.n_estimators))
        errors.extend(_require_positive_int("min_samples_leaf", self.min_samples_leaf))
        if self.max_depth is not None:
            errors.extend(_require_positive_int("max_depth", self.max_depth))
        return tuple(errors)


@dataclass(frozen=True)
class TrainingConfig:
    """Complete, reproducible contract of one training execution.

    A single ``random_seed`` drives both the split and the RandomForest so that
    one recorded value is enough to reproduce a run.
    """

    dataset: DatasetConfig
    task: TaskConfig = TaskConfig()
    split: SplitConfig = SplitConfig()
    forest: RandomForestConfig = RandomForestConfig()
    random_seed: int = DEFAULT_RANDOM_SEED

    def collect_errors(self) -> tuple[str, ...]:
        return (
            *self.dataset.collect_errors(),
            *self.task.collect_errors(),
            *self.split.collect_errors(),
            *self.forest.collect_errors(),
            *_require_int("random_seed", self.random_seed),
        )

    def validate(self) -> "TrainingConfig":
        errors = self.collect_errors()
        if errors:
            raise ConfigurationError(
                "Invalid training configuration:\n"
                + "\n".join(f"- {message}" for message in errors)
            )
        return self


@dataclass(frozen=True)
class ClearmlSettings:
    """ClearML connection settings, read from the environment only.

    Credentials are excluded from ``repr`` and must never be recorded as Task
    Parameters. When they are absent the ClearML SDK falls back to its own
    configuration file.
    """

    api_host: str = DEFAULT_API_HOST
    web_host: str = DEFAULT_WEB_HOST
    files_host: str = DEFAULT_FILES_HOST
    access_key: str | None = field(default=None, repr=False)
    secret_key: str | None = field(default=None, repr=False)

    @classmethod
    def from_environment(cls) -> "ClearmlSettings":
        return cls(
            api_host=os.getenv("CLEARML_API_HOST", DEFAULT_API_HOST).rstrip("/"),
            web_host=os.getenv("CLEARML_WEB_HOST", DEFAULT_WEB_HOST).rstrip("/"),
            files_host=os.getenv("CLEARML_FILES_HOST", DEFAULT_FILES_HOST).rstrip("/"),
            access_key=_optional_environment_value("CLEARML_API_ACCESS_KEY"),
            secret_key=_optional_environment_value("CLEARML_API_SECRET_KEY"),
        )

    @property
    def has_explicit_credentials(self) -> bool:
        return self.access_key is not None and self.secret_key is not None

    def collect_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        errors.extend(_require_text("api_host", self.api_host))
        errors.extend(_require_text("web_host", self.web_host))
        errors.extend(_require_text("files_host", self.files_host))
        if (self.access_key is None) != (self.secret_key is None):
            errors.append(
                "CLEARML_API_ACCESS_KEY and CLEARML_API_SECRET_KEY must be set together"
            )
        return tuple(errors)

    def validate(self) -> "ClearmlSettings":
        errors = self.collect_errors()
        if errors:
            raise ConfigurationError(
                "Invalid ClearML settings:\n"
                + "\n".join(f"- {message}" for message in errors)
            )
        return self


def _optional_environment_value(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _require_text(name: str, value: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        return (f"{name} is required",)
    return ()


def _require_relative_path(name: str, value: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        return (f"{name} is required",)
    if "\\" in value:
        return (f"{name} must use '/' as the path separator, but was {value!r}",)
    if value.startswith("/") or ntpath.isabs(value):
        return (f"{name} must be relative to the dataset root, but was {value!r}",)
    if ".." in PurePosixPath(value).parts:
        return (f"{name} must not contain '..', but was {value!r}",)
    return ()


def _require_int(name: str, value: int) -> tuple[str, ...]:
    if isinstance(value, bool) or not isinstance(value, int):
        return (f"{name} must be an integer, but was {value!r}",)
    return ()


def _require_positive_int(name: str, value: int) -> tuple[str, ...]:
    errors = _require_int(name, value)
    if errors:
        return errors
    if value <= 0:
        return (f"{name} must be greater than 0, but was {value}",)
    return ()


def _require_ratio(name: str, value: float) -> tuple[str, ...]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return (f"{name} must be a number, but was {value!r}",)
    if not math.isfinite(value):
        return (f"{name} must be a finite number, but was {value!r}",)
    if not 0.0 < value < 1.0:
        return (f"{name} must be greater than 0 and less than 1, but was {value}",)
    return ()
