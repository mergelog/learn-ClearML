"""Score the predictions of one run.

This module never contacts ClearML. It turns the predictions a run produced
into the metrics the Task records, and it is the only place the test part is
scored: the validation part confirmed the settings during training, and the
test part is predicted exactly once, here, for the final evaluation.

``fail`` is the positive label. A quality classifier earns its place by finding
the bad products, so precision, recall and F1 describe that class instead of
the majority ``pass`` class. The confusion matrix keeps the label order of the
data contract, so two runs stay comparable cell by cell.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from .domain import (
    LABELS,
    POSITIVE_LABEL,
    EvaluationResult,
    SplitPart,
    TrainingEvaluation,
)
from .train import TrainedModel


ACCURACY = "accuracy"
PRECISION = "precision"
RECALL = "recall"
F1 = "f1"

# The order the metrics are reported and written in, so a Task always lists
# them the same way.
METRIC_NAMES = (ACCURACY, PRECISION, RECALL, F1)


class EvaluationError(ValueError):
    """Raised when a split cannot be scored against the predictions it was given."""


def evaluate_model(model: TrainedModel) -> TrainingEvaluation:
    """Score the confirmed settings, then spend the test part exactly once."""
    return TrainingEvaluation(
        validation=evaluate_split(model.split.validation, model.validation_predictions),
        test=evaluate_split(model.split.test, model.predict(model.split.test)),
    )


def evaluate_split(part: SplitPart, predictions: np.ndarray) -> EvaluationResult:
    """Score one part of the split against the predictions made for it."""
    predicted = np.asarray(predictions)
    if predicted.shape[0] != part.row_count:
        raise EvaluationError(
            f"the {part.name} part holds {part.row_count} rows, but "
            f"{predicted.shape[0]} predictions were made for it"
        )

    return EvaluationResult(
        split_name=part.name,
        metrics=score(part.targets, predicted),
        confusion_matrix=confusion_matrix(part.targets, predicted, labels=LABELS),
        labels=LABELS,
    )


def score(targets: np.ndarray, predictions: np.ndarray) -> Mapping[str, float]:
    """Measure how well the predictions found the failing products.

    ``zero_division=0`` reports a run that predicted no failure at all as a
    recall of zero rather than as an error, so a badly configured run is still
    comparable to the others.
    """
    precision, recall, f1_score, _ = precision_recall_fscore_support(
        targets,
        predictions,
        average="binary",
        pos_label=POSITIVE_LABEL,
        zero_division=0,
    )
    return {
        ACCURACY: float(accuracy_score(targets, predictions)),
        PRECISION: float(precision),
        RECALL: float(recall),
        F1: float(f1_score),
    }
