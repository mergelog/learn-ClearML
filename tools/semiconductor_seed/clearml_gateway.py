from __future__ import annotations

import json
import pickle
import re
from pathlib import Path

from clearml import Dataset, OutputModel, Task

from .config import DATASET_NAME, PROJECT_ROOT, SEED_TAG, Settings
from .domain import ExperimentResult, ExperimentSpec, GeneratedDataset


class ClearmlGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        Task.set_credentials(
            api_host=settings.api_host,
            web_host=settings.web_host,
            files_host=settings.files_host,
            key=settings.access_key,
            secret=settings.secret_key,
        )

    def ensure_dataset(
        self,
        dataset: GeneratedDataset,
        parent_id: str | None = None,
    ) -> str:
        existing = self._find_dataset(dataset.definition.version)
        if existing is not None:
            return existing.id

        created = Dataset.create(
            dataset_project=PROJECT_ROOT,
            dataset_name=DATASET_NAME,
            dataset_version=dataset.definition.version,
            dataset_tags=(SEED_TAG,),
            parent_datasets=(parent_id,) if parent_id else None,
            output_uri=self.settings.files_host,
            description=dataset.definition.description,
        )
        created.add_files(dataset.csv_path)
        created.upload(show_progress=False, verbose=False)
        created.finalize(verbose=False)
        return created.id

    def experiment_exists(self, spec: ExperimentSpec) -> bool:
        project_name = self._project_name(spec)
        tasks = Task.get_tasks(
            project_name=project_name,
            task_name=f"^{re.escape(spec.name)}$",
            tags=(SEED_TAG,),
        )
        return any(task.name == spec.name for task in tasks)

    def register_experiment(
        self,
        spec: ExperimentSpec,
        dataset_id: str,
        result: ExperimentResult | None,
        artifact_dir: Path,
        random_seed: int,
    ) -> str:
        task = Task.create(
            project_name=self._project_name(spec),
            task_name=spec.name,
            task_type=Task.TaskTypes.training,
            packages=False,
            add_task_init_call=False,
            detect_repository=False,
        )
        task.add_tags((SEED_TAG, spec.model_kind, f"dataset-{spec.dataset_version}"))
        task.set_comment(self._task_comment(spec))
        task.set_parameters(
            {
                "General/model": spec.model_kind,
                "General/dataset_version": spec.dataset_version,
                "General/dataset_id": dataset_id,
                "General/random_seed": random_seed,
                "General/test_size": 0.25,
                **{
                    f"Model/{key}": value
                    for key, value in spec.parameters.items()
                },
            }
        )
        task.mark_started(force=True)
        logger = task.get_logger()

        if spec.final_status == "failed":
            logger.report_text(
                "Training failed: required feature 'inspection_value' was not found.",
            )
            task.mark_failed(
                status_reason="Missing required feature",
                status_message="Synthetic failure scenario for log inspection.",
                force=True,
            )
            task.close()
            return task.id

        if spec.final_status == "aborted":
            logger.report_text(
                "Parameter search was stopped before training to limit local resource usage.",
            )
            task.mark_stopped(
                force=True,
                status_message="Synthetic aborted scenario for status filtering.",
            )
            task.close()
            return task.id

        if result is None:
            raise ValueError(f"Result is required for completed experiment {spec.name}")

        for metric_name, value in result.metrics.items():
            logger.report_scalar("Evaluation", metric_name, value, iteration=0)
        logger.report_confusion_matrix(
            "Evaluation",
            "Confusion Matrix",
            matrix=result.confusion_matrix,
            iteration=0,
            xlabels=["pass", "fail"],
            ylabels=["pass", "fail"],
            comment="Rows are actual labels; columns are predicted labels.",
        )

        experiment_dir = artifact_dir / spec.name
        experiment_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = experiment_dir / "evaluation.json"
        metrics_path.write_text(
            json.dumps(
                {
                    "metrics": result.metrics,
                    "confusion_matrix": result.confusion_matrix.tolist(),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        task.upload_artifact(
            "evaluation",
            artifact_object=str(metrics_path),
            metadata={"dataset_version": spec.dataset_version},
            wait_on_upload=True,
        )

        if spec.register_model:
            model_path = experiment_dir / "model.pkl"
            model_path.write_bytes(pickle.dumps(result.model))
            output_model = OutputModel(
                task=task,
                name=f"quality-prediction-{spec.name}",
                tags=[SEED_TAG, "quality-classifier"],
                comment="Synthetic model for local ClearML learning.",
                label_enumeration={"pass": 0, "fail": 1},
            )
            output_model.update_weights(
                weights_filename=str(model_path),
                auto_delete_file=False,
                async_enable=False,
            )

        task.flush(wait_for_uploads=True)
        task.mark_completed(
            status_message="Synthetic semiconductor quality experiment completed.",
            force=True,
        )
        task.close()
        return task.id

    def _find_dataset(self, version: str) -> Dataset | None:
        try:
            return Dataset.get(
                dataset_project=PROJECT_ROOT,
                dataset_name=DATASET_NAME,
                dataset_version=version,
                dataset_tags=(SEED_TAG,),
                only_completed=True,
            )
        except ValueError:
            return None

    @staticmethod
    def _project_name(spec: ExperimentSpec) -> str:
        return f"{PROJECT_ROOT}/{spec.group}"

    @staticmethod
    def _task_comment(spec: ExperimentSpec) -> str:
        return (
            "Synthetic semiconductor quality classification experiment. "
            f"Model={spec.model_kind}, dataset={spec.dataset_version}."
        )

