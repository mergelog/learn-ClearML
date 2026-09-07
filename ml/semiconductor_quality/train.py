"""Fit the RandomForest of one execution.

This module never contacts ClearML. It holds the training use case: split the
validated input, build one pipeline out of the preprocessing and the forest,
fit it, and confirm the settings of the run on the validation part.

Two boundaries are deliberate. The pipeline is fitted on the training rows
only, so neither the validation nor the test part can leak into what the model
learned. And the test part is not predicted here at all: it stays untouched
until the final evaluation, which uses it exactly once. A validation result
that looks wrong is a reason to start another Task with other parameters, not
to refit inside this one.

Storing the fitted pipeline lives here as well, because what is stored is the
model of this module: the preprocessing and the forest as one unit. Handing
the stored file to an experiment tracker is somebody else's job.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from .config import RandomForestConfig, TrainingConfig
from .domain import (
    DataSplit,
    DatasetValidationReport,
    SplitPart,
    TrainingInput,
)
from .preprocess import build_preprocessor, split_training_input


PREPROCESSOR_STEP = "preprocessor"
CLASSIFIER_STEP = "classifier"

MODEL_FILE_NAME = "semiconductor_quality_pipeline.joblib"


@dataclass(frozen=True)
class TrainedModel:
    """Outcome of one fit: what it learned from, and what it predicted so far."""

    report: DatasetValidationReport
    split: DataSplit
    pipeline: Pipeline
    validation_predictions: np.ndarray

    def predict(self, part: SplitPart) -> np.ndarray:
        """Predict one part with the fitted pipeline, preprocessing included."""
        return predict_part(self.pipeline, part)


def train_classifier(training_input: TrainingInput, config: TrainingConfig) -> TrainedModel:
    """Split the validated input, fit the forest, and confirm it on validation."""
    split = split_training_input(training_input, config.split, config.random_seed)
    pipeline = build_pipeline(training_input.report, config.forest, config.random_seed)
    fit_pipeline(pipeline, split.train)
    return TrainedModel(
        report=training_input.report,
        split=split,
        pipeline=pipeline,
        validation_predictions=predict_part(pipeline, split.validation),
    )


def build_pipeline(
    report: DatasetValidationReport,
    forest: RandomForestConfig,
    random_seed: int,
) -> Pipeline:
    """Put the preprocessing and the forest into a single fitted unit.

    Keeping both in one pipeline means the preprocessing is fitted on the
    training rows only, and that a stored model carries the preprocessing it
    was fitted with.
    """
    return Pipeline(
        steps=[
            (PREPROCESSOR_STEP, build_preprocessor(report)),
            (CLASSIFIER_STEP, build_classifier(forest, random_seed)),
        ]
    )


def build_classifier(forest: RandomForestConfig, random_seed: int) -> RandomForestClassifier:
    """Build the forest of the run, seeded so that a rerun repeats it."""
    return RandomForestClassifier(
        n_estimators=forest.n_estimators,
        max_depth=forest.max_depth,
        min_samples_leaf=forest.min_samples_leaf,
        random_state=random_seed,
        n_jobs=-1,
    )


def fit_pipeline(pipeline: Pipeline, train: SplitPart) -> Pipeline:
    """Fit the pipeline on the training part, and on nothing else."""
    return pipeline.fit(train.features, train.targets)


def predict_part(pipeline: Pipeline, part: SplitPart) -> np.ndarray:
    return np.asarray(pipeline.predict(part.features))


@contextmanager
def saved_pipeline(pipeline: Pipeline, file_name: str = MODEL_FILE_NAME) -> Iterator[Path]:
    """Write the fitted pipeline to a file for as long as a caller needs it.

    The preprocessing is stored together with the forest, so the file is the
    whole model and not the classifier alone. It is written into a temporary
    directory because it exists only to be handed over, and whoever receives it
    is expected to have taken its copy before this context closes.
    """
    with TemporaryDirectory(prefix="semiconductor-quality-") as directory:
        path = Path(directory) / file_name
        joblib.dump(pipeline, path)
        yield path
