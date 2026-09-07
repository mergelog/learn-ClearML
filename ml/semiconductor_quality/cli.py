"""Command line contract of the training run.

Parsing builds the execution contract and validates it offline, so a malformed
invocation is rejected before :mod:`clearml_tracking` creates a ClearML Task.
The arguments are kept alongside the resolved contract, because the Task
records both how the run was asked for and what it resolved to.

This module is also the composition root of a run: it connects the ClearML
boundary to the data preparation, and turns the outcome into a process exit
code. It deliberately holds no data handling or evaluation of its own.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .clearml_tracking import fetch_dataset, training_task
from .config import (
    DEFAULT_DATASET_CSV_PATH,
    DEFAULT_DATASET_NAME,
    DEFAULT_DATASET_PROJECT,
    DEFAULT_RANDOM_SEED,
    DEFAULT_TASK_NAME,
    DEFAULT_TASK_PROJECT,
    ConfigurationError,
    DatasetConfig,
    RandomForestConfig,
    SplitConfig,
    TaskConfig,
    TrainingConfig,
)
from .dataset import load_training_input
from .domain import (
    DatasetValidationReport,
    EvaluationResult,
    SplitPart,
    TrainingEvaluation,
)
from .evaluate import evaluate_model
from .train import TrainedModel, saved_pipeline, train_classifier


SPLIT_DEFAULTS = SplitConfig()
FOREST_DEFAULTS = RandomForestConfig()

# ``pnpm run ml:train -- --dataset-version 1.0.0`` forwards the separator itself,
# so the script has to recognise it as the package manager's and not as its own.
ARGUMENT_SEPARATOR = "--"

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_INVALID_USAGE = 2
EXIT_INTERRUPTED = 130


@dataclass(frozen=True)
class TrainingCommand:
    """One parsed invocation: the contract to run, and the arguments it came from."""

    config: TrainingConfig
    command_line: tuple[str, ...]


@dataclass(frozen=True)
class TrainingOutcome:
    """What one execution produced, and the ClearML Task it was recorded on."""

    task_id: str
    model: TrainedModel
    evaluation: TrainingEvaluation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Train a semiconductor quality classifier from a registered ClearML "
            "Dataset version and track the run as a ClearML Task."
        ),
    )

    dataset_group = parser.add_argument_group("dataset")
    dataset_group.add_argument(
        "--dataset-version",
        required=True,
        help="Version of the registered ClearML Dataset to train on. Never inferred.",
    )
    dataset_group.add_argument(
        "--dataset-project",
        default=DEFAULT_DATASET_PROJECT,
        help="ClearML project the Dataset belongs to.",
    )
    dataset_group.add_argument(
        "--dataset-name",
        default=DEFAULT_DATASET_NAME,
        help="Name of the registered ClearML Dataset.",
    )
    dataset_group.add_argument(
        "--dataset-csv-path",
        default=DEFAULT_DATASET_CSV_PATH,
        help="CSV to read, relative to the root of the fetched Dataset.",
    )

    task_group = parser.add_argument_group("task")
    task_group.add_argument(
        "--task-project",
        default=DEFAULT_TASK_PROJECT,
        help="ClearML project the training Task is created in.",
    )
    task_group.add_argument(
        "--task-name",
        default=DEFAULT_TASK_NAME,
        help="Name of the training Task.",
    )

    split_group = parser.add_argument_group("split")
    split_group.add_argument(
        "--train-ratio",
        type=float,
        default=SPLIT_DEFAULTS.train_ratio,
        help="Share of the rows used to fit the model.",
    )
    split_group.add_argument(
        "--validation-ratio",
        type=float,
        default=SPLIT_DEFAULTS.validation_ratio,
        help="Share of the rows used to confirm the settings of the run.",
    )
    split_group.add_argument(
        "--test-ratio",
        type=float,
        default=SPLIT_DEFAULTS.test_ratio,
        help="Share of the rows kept for the final evaluation.",
    )

    forest_group = parser.add_argument_group("random forest")
    forest_group.add_argument(
        "--n-estimators",
        type=int,
        default=FOREST_DEFAULTS.n_estimators,
        help="Number of trees in the forest.",
    )
    forest_group.add_argument(
        "--max-depth",
        type=int,
        default=FOREST_DEFAULTS.max_depth,
        help="Maximum depth of a tree. Omit to grow the trees without a limit.",
    )
    forest_group.add_argument(
        "--min-samples-leaf",
        type=int,
        default=FOREST_DEFAULTS.min_samples_leaf,
        help="Minimum number of samples required at a leaf.",
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Seed shared by the split and the forest, so a run stays reproducible.",
    )
    return parser


def parse_arguments(argv: Sequence[str]) -> TrainingCommand:
    """Build the execution contract of one invocation, or reject the invocation."""
    arguments = build_parser().parse_args(list(argv))
    config = TrainingConfig(
        dataset=DatasetConfig(
            dataset_version=arguments.dataset_version,
            dataset_project=arguments.dataset_project,
            dataset_name=arguments.dataset_name,
            dataset_csv_path=arguments.dataset_csv_path,
        ),
        task=TaskConfig(
            task_project=arguments.task_project,
            task_name=arguments.task_name,
        ),
        split=SplitConfig(
            train_ratio=arguments.train_ratio,
            validation_ratio=arguments.validation_ratio,
            test_ratio=arguments.test_ratio,
        ),
        forest=RandomForestConfig(
            n_estimators=arguments.n_estimators,
            max_depth=arguments.max_depth,
            min_samples_leaf=arguments.min_samples_leaf,
        ),
        random_seed=arguments.random_seed,
    )
    return TrainingCommand(config=config.validate(), command_line=tuple(argv))


def run_training(command: TrainingCommand) -> TrainingOutcome:
    """Run one tracked execution, from the started Task to the registered model.

    Everything inside the boundary is attributed to a single ClearML Task, so a
    Dataset version that cannot be resolved, an input that fails validation or
    a fit that raises is left behind as a failed Task rather than as no Task at
    all. The Task is completed only after the last upload, which is why the
    model is registered while the boundary is still open.
    """
    config = command.config
    with training_task(config, command_line=command.command_line) as task:
        fetched = fetch_dataset(config.dataset)
        training_input = load_training_input(fetched, config.dataset.dataset_csv_path)
        task.record_dataset_source(training_input.report.source)

        model = train_classifier(training_input, config)
        task.record_input(model.report, model.split)

        evaluation = evaluate_model(model)
        task.record_evaluation(evaluation)

        with saved_pipeline(model.pipeline) as weights:
            task.register_model(weights)

        return TrainingOutcome(task_id=task.id, model=model, evaluation=evaluation)


def main(argv: Sequence[str] | None = None) -> int:
    """Run one training command and report its outcome as an exit code."""
    arguments = _forwarded_arguments(sys.argv[1:] if argv is None else argv)
    try:
        command = parse_arguments(arguments)
    except ConfigurationError as error:
        print(error, file=sys.stderr)
        return EXIT_INVALID_USAGE

    try:
        outcome = run_training(command)
    except KeyboardInterrupt:
        print("Training was interrupted before it completed.", file=sys.stderr)
        return EXIT_INTERRUPTED
    except Exception as error:  # noqa: BLE001 - the reason is reported, not swallowed
        print(f"Training failed: {error}", file=sys.stderr)
        return EXIT_FAILURE

    print(_describe(outcome))
    return EXIT_SUCCESS


def _forwarded_arguments(argv: Sequence[str]) -> list[str]:
    """Drop the separator a package manager puts in front of the arguments.

    Without this, argparse would read the leading ``--`` as "the rest are
    positional" and reject an otherwise valid invocation. Removing it keeps the
    documented pnpm command and a direct call to the module equivalent.
    """
    arguments = list(argv)
    if arguments and arguments[0] == ARGUMENT_SEPARATOR:
        del arguments[0]
    return arguments


def _describe(outcome: TrainingOutcome) -> str:
    model = outcome.model
    parts = " ".join(_describe_part(part) for part in model.split.parts)
    return "\n".join(
        (
            _describe_dataset(model.report),
            f"Trained on {parts}",
            *(_describe_result(result) for result in outcome.evaluation.results),
            f"Recorded as ClearML Task {outcome.task_id}",
        )
    )


def _describe_result(result: EvaluationResult) -> str:
    scores = " ".join(f"{name}={value:.4f}" for name, value in result.metrics.items())
    return f"{result.split_name}: {scores}"


def _describe_dataset(report: DatasetValidationReport) -> str:
    return (
        f"Dataset {report.source.dataset_name} {report.source.dataset_version} "
        f"({report.source.dataset_id}) validated: "
        f"{report.row_count} rows, {len(report.feature_names)} features, "
        f"{_describe_labels(report.label_counts)}"
    )


def _describe_part(part: SplitPart) -> str:
    return f"{part.name}={part.row_count} ({_describe_labels(part.label_counts)})"


def _describe_labels(label_counts: Mapping[str, int]) -> str:
    return ", ".join(f"{label}={count}" for label, count in label_counts.items())


if __name__ == "__main__":
    raise SystemExit(main())
