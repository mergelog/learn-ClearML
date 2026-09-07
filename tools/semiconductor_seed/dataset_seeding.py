from __future__ import annotations

from typing import Protocol

from .config import Settings
from .domain import GeneratedDataset
from .generator import DATASET_VERSIONS, generate_dataset


class DatasetGateway(Protocol):
    def ensure_dataset(
        self,
        dataset: GeneratedDataset,
        parent_id: str | None = None,
    ) -> str: ...


def seed_datasets(
    settings: Settings,
    gateway: DatasetGateway,
) -> tuple[dict[str, GeneratedDataset], dict[str, str]]:
    datasets = {
        definition.version: generate_dataset(
            definition,
            settings.output_dir / "datasets",
            settings.random_seed,
        )
        for definition in DATASET_VERSIONS
    }

    dataset_ids: dict[str, str] = {}
    parent_id: str | None = None
    for definition in DATASET_VERSIONS:
        dataset_id = gateway.ensure_dataset(
            datasets[definition.version],
            parent_id=parent_id,
        )
        dataset_ids[definition.version] = dataset_id
        parent_id = dataset_id
        print(f"Dataset ready: {definition.version} ({dataset_id})")

    return datasets, dataset_ids
