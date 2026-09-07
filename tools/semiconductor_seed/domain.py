from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class DatasetVersion:
    version: str
    row_count: int
    random_seed_offset: int
    description: str


@dataclass(frozen=True)
class GeneratedDataset:
    definition: DatasetVersion
    csv_path: Path
    features: np.ndarray
    targets: np.ndarray


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    group: str
    dataset_version: str
    model_kind: str
    parameters: dict[str, object]
    final_status: str = "completed"
    register_model: bool = False


@dataclass(frozen=True)
class ExperimentResult:
    metrics: dict[str, float]
    confusion_matrix: np.ndarray
    model: object

