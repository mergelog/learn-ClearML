from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class InventoryItem:
    name: str
    project: str
    created_at: datetime | None
    item_id: str
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ClearmlDataStatus:
    api_host: str
    project_root: str
    total_projects: int
    total_tasks: int
    total_models: int
    projects: tuple[InventoryItem, ...]
    datasets: tuple[InventoryItem, ...]
    training_tasks: tuple[InventoryItem, ...]
    other_tasks: tuple[InventoryItem, ...]
    models: tuple[InventoryItem, ...]

    @property
    def has_learning_data(self) -> bool:
        return bool(
            self.projects
            or self.datasets
            or self.training_tasks
            or self.other_tasks
            or self.models
        )
