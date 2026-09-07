"""ClearML SDK boundary of the training flow.

Every call into the ClearML SDK is made from this module, so the data
preparation, training and evaluation steps stay free of the SDK and can be
exercised without a ClearML Server.

The boundary is opened before the Dataset is fetched. A run that fails while
resolving the Dataset, validating the input or fitting the model is therefore
recorded as a failed ClearML Task instead of leaving no trace at all.

Model registration is an explicit step of this flow, so the scikit-learn and
joblib automatic model tracking of the SDK is turned off. Parameters are
recorded explicitly for the same reason, so the automatic argument parser
binding is turned off as well and the recorded contract has a single source.
Credentials are taken from ``ClearmlSettings`` and are never recorded as Task
Parameters.

The execution dependencies are recorded explicitly from
``tools/requirements.txt``. Resolving that file from this module keeps the
recorded contract independent of the directory from which training is started.
"""

from __future__ import annotations

import shlex
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from clearml import Dataset, Logger, OutputModel, Task
from clearml.model import Framework

from .config import ClearmlSettings, DatasetConfig, TrainingConfig
from .domain import (
    LABELS,
    DataSplit,
    DatasetSource,
    DatasetValidationReport,
    EvaluationResult,
    FetchedDataset,
    TrainingEvaluation,
)


DISABLED_MODEL_FRAMEWORKS: Mapping[str, bool] = {"scikit": False, "joblib": False}
REQUIREMENTS_FILE = Path(__file__).resolve().parents[2] / "tools" / "requirements.txt"

DATASET_SECTION = "Dataset"
RESOLVED_DATASET_SECTION = "Resolved Dataset"
SPLIT_SECTION = "Split"
FOREST_SECTION = "RandomForest"
EXECUTION_SECTION = "Execution"

DATA_VALIDATION_ARTIFACT = "data_validation"
EVALUATION_ARTIFACT = "evaluation"

# One execution reports one final figure per metric, so every value of a run
# shares the same iteration and the Web UI compares runs, not steps.
METRICS_ITERATION = 0
CONFUSION_MATRIX_TITLE = "Confusion Matrix"
CONFUSION_MATRIX_COMMENT = "Rows are actual labels; columns are predicted labels."

MODEL_NAME = "semiconductor-quality-classifier"
MODEL_COMMENT = "RandomForest pipeline, including the preprocessing it was fitted with."
MODEL_LABEL_ENUMERATION: Mapping[str, int] = {
    label: index for index, label in enumerate(LABELS)
}


class TrainingTask:
    """A started ClearML Task, closed exactly once with an explicit outcome."""

    def __init__(self, task: Task) -> None:
        self._task = task
        self._closed = False

    @property
    def id(self) -> str:
        return str(self._task.id)

    def record_configuration(
        self,
        config: TrainingConfig,
        command_line: Sequence[str] = (),
    ) -> None:
        """Track how the run was invoked and which contract it resolved to."""
        self._task.connect(asdict(config.dataset), name=DATASET_SECTION)
        self._task.connect(asdict(config.split), name=SPLIT_SECTION)
        self._task.connect(asdict(config.forest), name=FOREST_SECTION)
        self._task.connect(
            {
                "command_line": shlex.join(command_line),
                "random_seed": config.random_seed,
            },
            name=EXECUTION_SECTION,
        )

    def record_dataset_source(self, source: DatasetSource) -> None:
        """Record which Dataset version the run resolved, next to the one it asked for.

        The Dataset alias already links Task and Dataset inside ClearML. The id
        is recorded here as well, so the Task alone still answers which data it
        learned from once the alias link is followed no further.
        """
        self._task.connect(
            {
                "dataset_id": source.dataset_id,
                "dataset_project": source.dataset_project,
                "dataset_name": source.dataset_name,
                "dataset_version": source.dataset_version,
                "csv_path": str(source.csv_path),
            },
            name=RESOLVED_DATASET_SECTION,
        )

    def record_input(self, report: DatasetValidationReport, split: DataSplit) -> None:
        """Upload what the run learned from, and how it was divided.

        The features are part of the payload, because the execution contract
        records which Dataset was read but not which of its columns a model was
        allowed to see.
        """
        self._upload_json(DATA_VALIDATION_ARTIFACT, _describe_input(report, split))

    def record_evaluation(self, evaluation: TrainingEvaluation) -> None:
        """Report every scored split under its own series, and keep the numbers.

        The scalars and the confusion matrices are what the Web UI compares
        between runs. The artifact holds the same figures as a readable file,
        so a result stays available once a plot has been left behind.
        """
        logger = self._task.get_logger()
        for result in evaluation.results:
            _report_result(logger, result)
        self._upload_json(EVALUATION_ARTIFACT, _describe_evaluation(evaluation))

    def register_model(self, weights: Path) -> None:
        """Attach the fitted pipeline as the single Output Model of this Task.

        The automatic scikit-learn and joblib tracking is disabled at ``init``,
        so this is the only place a model is registered and a Task cannot end
        up holding the same pipeline twice.
        """
        model = OutputModel(
            task=self._task,
            name=MODEL_NAME,
            framework=Framework.scikitlearn,
            label_enumeration=dict(MODEL_LABEL_ENUMERATION),
            comment=MODEL_COMMENT,
        )
        model.update_weights(
            weights_filename=str(weights),
            auto_delete_file=False,
            async_enable=False,
        )

    def _upload_json(self, name: str, content: dict[str, object]) -> None:
        # ``auto_pickle=False`` turns a payload that cannot be serialised into a
        # failure, instead of a pickle nobody can read from the Web UI. The
        # upload is awaited so that the caller may delete what it handed over.
        self._task.upload_artifact(
            name,
            artifact_object=content,
            wait_on_upload=True,
            auto_pickle=False,
            sort_keys=False,
        )

    def complete(self) -> None:
        """Wait for every upload to finish, then close the Task as completed."""
        if self._closed:
            return
        self._closed = True
        self._task.flush(wait_for_uploads=True)
        self._task.close()

    def fail(self, error: Exception) -> None:
        """Close the Task as failed, with the reason left on the Task log."""
        if self._closed:
            return
        self._closed = True
        self._task.get_logger().report_text(f"Training failed: {error}")
        self._task.mark_failed(
            status_reason=type(error).__name__,
            status_message=str(error),
            force=True,
        )
        self._task.close()


def start_training_task(
    config: TrainingConfig,
    *,
    settings: ClearmlSettings | None = None,
    command_line: Sequence[str] = (),
) -> TrainingTask:
    """Validate the execution contract offline, then create one new Task.

    ``reuse_last_task_id=False`` keeps every execution a separate Task, so two
    runs of the same project and Task name stay comparable.
    """
    config.validate()
    connection = (settings or ClearmlSettings.from_environment()).validate()
    _apply_connection_settings(connection)

    task = Task.init(
        project_name=config.task.task_project,
        task_name=config.task.task_name,
        task_type=Task.TaskTypes.training,
        reuse_last_task_id=False,
        auto_connect_arg_parser=False,
        auto_connect_frameworks=dict(DISABLED_MODEL_FRAMEWORKS),
        output_uri=connection.files_host,
    )
    task.set_packages(str(REQUIREMENTS_FILE))
    training_task = TrainingTask(task)
    training_task.record_configuration(config, command_line=command_line)
    return training_task


@contextmanager
def training_task(
    config: TrainingConfig,
    *,
    settings: ClearmlSettings | None = None,
    command_line: Sequence[str] = (),
) -> Iterator[TrainingTask]:
    """Execution boundary of one run.

    The Task exists before the caller reads the Dataset, and the run leaves the
    boundary either completed or failed. ``KeyboardInterrupt`` is deliberately
    not turned into a failure, so a manually stopped run is reported as stopped
    by the SDK itself.
    """
    task = start_training_task(config, settings=settings, command_line=command_line)
    try:
        yield task
    except Exception as error:
        task.fail(error)
        raise
    task.complete()


def fetch_dataset(config: DatasetConfig) -> FetchedDataset:
    """Resolve the requested Dataset version and download its read-only copy.

    The version is always given, so a run never silently follows the latest
    Dataset. ``alias`` makes ClearML link the resolved Dataset to the Task that
    is already running, which is why this is called inside the Task boundary.
    """
    dataset = Dataset.get(
        dataset_project=config.dataset_project,
        dataset_name=config.dataset_name,
        dataset_version=config.dataset_version,
        alias=config.dataset_alias,
        only_completed=True,
    )
    return FetchedDataset(
        dataset_id=str(dataset.id),
        dataset_project=config.dataset_project,
        dataset_name=str(dataset.name or config.dataset_name),
        dataset_version=str(dataset.version or config.dataset_version),
        local_root=Path(dataset.get_local_copy()),
    )


def _describe_input(report: DatasetValidationReport, split: DataSplit) -> dict[str, object]:
    return {
        "dataset": {
            "id": report.source.dataset_id,
            "project": report.source.dataset_project,
            "name": report.source.dataset_name,
            "version": report.source.dataset_version,
            "csv_path": str(report.source.csv_path),
        },
        "row_count": report.row_count,
        "features": {
            "all": list(report.feature_names),
            "numeric": list(report.numeric_feature_names),
            "categorical": list(report.categorical_feature_names),
        },
        "label_counts": dict(report.label_counts),
        "split": {
            part.name: {
                "row_count": part.row_count,
                "label_counts": dict(part.label_counts),
            }
            for part in split.parts
        },
    }


def _describe_evaluation(evaluation: TrainingEvaluation) -> dict[str, object]:
    return {result.split_name: _describe_result(result) for result in evaluation.results}


def _describe_result(result: EvaluationResult) -> dict[str, object]:
    return {
        "metrics": {name: float(value) for name, value in result.metrics.items()},
        "labels": list(result.labels),
        "confusion_matrix": result.confusion_matrix.tolist(),
        "confusion_matrix_layout": CONFUSION_MATRIX_COMMENT,
    }


def _report_result(logger: Logger, result: EvaluationResult) -> None:
    for name, value in result.metrics.items():
        logger.report_scalar(
            title=name,
            series=result.split_name,
            value=float(value),
            iteration=METRICS_ITERATION,
        )
    logger.report_confusion_matrix(
        title=CONFUSION_MATRIX_TITLE,
        series=result.split_name,
        matrix=result.confusion_matrix,
        iteration=METRICS_ITERATION,
        xlabels=list(result.labels),
        ylabels=list(result.labels),
        comment=CONFUSION_MATRIX_COMMENT,
    )


def _apply_connection_settings(settings: ClearmlSettings) -> None:
    """Point the SDK at the configured server.

    Blank credentials are ignored by the SDK, which then falls back to its own
    configuration file.
    """
    Task.set_credentials(
        api_host=settings.api_host,
        web_host=settings.web_host,
        files_host=settings.files_host,
        key=settings.access_key,
        secret=settings.secret_key,
    )
