from __future__ import annotations

import time

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .domain import ExperimentResult, ExperimentSpec, GeneratedDataset


NUMERIC_COLUMNS = list(range(7))
CATEGORICAL_COLUMNS = [7, 8]


def train_experiment(
    spec: ExperimentSpec,
    dataset: GeneratedDataset,
    random_seed: int,
) -> ExperimentResult:
    features_train, features_test, targets_train, targets_test = train_test_split(
        dataset.features,
        dataset.targets,
        test_size=0.25,
        random_state=random_seed,
        stratify=dataset.targets,
    )
    model = _build_pipeline(spec, random_seed)

    started_at = time.perf_counter()
    model.fit(features_train, targets_train)
    training_seconds = time.perf_counter() - started_at

    started_at = time.perf_counter()
    predictions = model.predict(features_test)
    inference_seconds = time.perf_counter() - started_at

    precision, recall, f1_score, _ = precision_recall_fscore_support(
        targets_test,
        predictions,
        average="binary",
        pos_label="fail",
        zero_division=0,
    )
    metrics = {
        "accuracy": float(accuracy_score(targets_test, predictions)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1_score),
        "training_seconds": training_seconds,
        "inference_seconds": inference_seconds,
    }
    matrix = confusion_matrix(targets_test, predictions, labels=("pass", "fail"))
    return ExperimentResult(metrics=metrics, confusion_matrix=matrix, model=model)


def _build_pipeline(spec: ExperimentSpec, random_seed: int) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=(
            ("numeric", StandardScaler(), NUMERIC_COLUMNS),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_COLUMNS,
            ),
        )
    )

    if spec.model_kind == "baseline":
        classifier = DummyClassifier(strategy="most_frequent")
    elif spec.model_kind == "logistic":
        classifier = LogisticRegression(
            C=float(spec.parameters["c"]),
            max_iter=500,
            random_state=random_seed,
        )
    elif spec.model_kind == "tree":
        classifier = DecisionTreeClassifier(
            max_depth=spec.parameters["max_depth"],
            min_samples_leaf=8,
            random_state=random_seed,
        )
    elif spec.model_kind == "forest":
        classifier = RandomForestClassifier(
            n_estimators=int(spec.parameters["n_estimators"]),
            max_depth=spec.parameters["max_depth"],
            min_samples_leaf=4,
            n_jobs=-1,
            random_state=random_seed,
        )
    else:
        raise ValueError(f"Unsupported trainable model kind: {spec.model_kind}")

    return Pipeline((('preprocessor', preprocessor), ('classifier', classifier)))

