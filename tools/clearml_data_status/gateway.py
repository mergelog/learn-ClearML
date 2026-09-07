from __future__ import annotations

from collections.abc import Callable
from typing import Any

from clearml import Task
from clearml.backend_api.session.client import APIClient

from tools.clearml_data_status.domain import ClearmlDataStatus, InventoryItem
from tools.semiconductor_seed.config import PROJECT_ROOT, Settings


PAGE_SIZE = 500
DATASET_SYSTEM_TAG = "dataset"
TRAINING_TASK_TYPE = "training"


def fetch_status(settings: Settings | None = None) -> ClearmlDataStatus:
    connection = settings or Settings.from_environment()
    Task.set_credentials(
        api_host=connection.api_host,
        web_host=connection.web_host,
        files_host=connection.files_host,
        key=connection.access_key,
        secret=connection.secret_key,
    )
    return collect_status(APIClient(), connection.api_host)


def collect_status(client: Any, api_host: str) -> ClearmlDataStatus:
    projects = _fetch_all(client.projects.get_all)
    tasks = _fetch_all(client.tasks.get_all)
    models = _fetch_all(client.models.get_all)

    referenced_projects = _fetch_referenced_projects(
        client,
        projects,
        (*tasks, *models),
    )
    all_known_projects = (*projects, *referenced_projects)
    matching_projects = tuple(
        project
        for project in all_known_projects
        if _belongs_to_project_root(str(project.name), PROJECT_ROOT)
    )
    project_names = {
        str(project.id): str(project.name)
        for project in matching_projects
    }
    project_ids = set(project_names)

    matching_tasks = tuple(
        task for task in tasks if str(task.project) in project_ids
    )
    dataset_tasks = tuple(
        task
        for task in matching_tasks
        if DATASET_SYSTEM_TAG in (getattr(task, "system_tags", None) or ())
    )
    dataset_task_ids = {str(task.id) for task in dataset_tasks}
    training_tasks = tuple(
        task
        for task in matching_tasks
        if str(task.id) not in dataset_task_ids
        and str(getattr(task, "type", "")) == TRAINING_TASK_TYPE
    )
    training_task_ids = {str(task.id) for task in training_tasks}
    other_tasks = tuple(
        task
        for task in matching_tasks
        if str(task.id) not in dataset_task_ids
        and str(task.id) not in training_task_ids
    )
    matching_models = tuple(
        model for model in models if str(model.project) in project_ids
    )

    return ClearmlDataStatus(
        api_host=api_host,
        project_root=PROJECT_ROOT,
        total_projects=len(projects),
        total_tasks=len(tasks),
        total_models=len(models),
        # Infrastructure projects are resolved so their Dataset Tasks can be
        # classified, but they are intentionally not presented as normal Projects.
        projects=tuple(
            _project_item(project)
            for project in _sort_by_created(
                tuple(
                    project
                    for project in projects
                    if _belongs_to_project_root(str(project.name), PROJECT_ROOT)
                )
            )
        ),
        datasets=tuple(
            _task_item(task, project_names, include_version=True)
            for task in _sort_by_created(dataset_tasks)
        ),
        training_tasks=tuple(
            _task_item(task, project_names)
            for task in _sort_by_created(training_tasks)
        ),
        other_tasks=tuple(
            _task_item(task, project_names)
            for task in _sort_by_created(other_tasks)
        ),
        models=tuple(
            _model_item(model, project_names)
            for model in _sort_by_created(matching_models)
        ),
    )


def _fetch_referenced_projects(
    client: Any,
    listed_projects: list[Any],
    project_owners: tuple[Any, ...],
) -> tuple[Any, ...]:
    """Resolve projects omitted from ``get_all``, including Dataset projects.

    ClearML hides infrastructure projects such as ``.datasets`` from the regular
    projects listing. Tasks still contain those project IDs, and ``get_by_id`` can
    resolve them individually.
    """
    listed_ids = {str(project.id) for project in listed_projects}
    referenced_ids = {
        str(owner.project)
        for owner in project_owners
        if getattr(owner, "project", None) is not None
    }

    resolved: list[Any] = []
    for project_id in sorted(referenced_ids - listed_ids):
        project = client.projects.get_by_id(project=project_id)
        if project is not None:
            resolved.append(project)
    return tuple(resolved)


def _fetch_all(fetch_page: Callable[..., list[Any]]) -> list[Any]:
    records: list[Any] = []
    page = 0
    while True:
        batch = list(fetch_page(page=page, page_size=PAGE_SIZE))
        records.extend(batch)
        if len(batch) < PAGE_SIZE:
            return records
        page += 1


def _belongs_to_project_root(project_name: str, project_root: str) -> bool:
    return project_name == project_root or project_name.startswith(f"{project_root}/")


def _project_item(project: Any) -> InventoryItem:
    return InventoryItem(
        name=str(project.name),
        project=str(project.name),
        created_at=getattr(project, "created", None),
        item_id=str(project.id),
    )


def _task_item(
    task: Any,
    project_names: dict[str, str],
    *,
    include_version: bool = False,
) -> InventoryItem:
    attributes: list[tuple[str, str]] = []
    if include_version:
        version = (getattr(task, "runtime", None) or {}).get("version")
        attributes.append(("version", str(version or "不明")))
    attributes.extend(
        (
            ("status", str(getattr(task, "status", None) or "不明")),
            ("type", str(getattr(task, "type", None) or "不明")),
        )
    )
    project_id = str(task.project)
    return InventoryItem(
        name=str(task.name),
        project=project_names.get(project_id, project_id),
        created_at=getattr(task, "created", None),
        item_id=str(task.id),
        attributes=tuple(attributes),
    )


def _model_item(model: Any, project_names: dict[str, str]) -> InventoryItem:
    project_id = str(model.project)
    return InventoryItem(
        name=str(model.name),
        project=project_names.get(project_id, project_id),
        created_at=getattr(model, "created", None),
        item_id=str(model.id),
        attributes=(
            ("framework", str(getattr(model, "framework", None) or "不明")),
        ),
    )


def _sort_by_created(records: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(
        sorted(
            records,
            key=lambda record: (
                getattr(record, "created", None) is None,
                str(getattr(record, "created", "")),
                str(getattr(record, "id", "")),
            ),
        )
    )
