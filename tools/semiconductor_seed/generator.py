from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .domain import DatasetVersion, GeneratedDataset


CSV_HEADERS = (
    "sample_id",
    "equipment_id",
    "process_step",
    "temperature",
    "pressure",
    "process_time",
    "gas_flow",
    "sensor_1",
    "sensor_2",
    "inspection_value",
    "result",
)

FEATURE_NAMES = (
    "temperature",
    "pressure",
    "process_time",
    "gas_flow",
    "sensor_1",
    "sensor_2",
    "inspection_value",
    "equipment_id",
    "process_step",
)

DATASET_VERSIONS = (
    DatasetVersion(
        version="1.0.0",
        row_count=1_200,
        random_seed_offset=0,
        description="Basic synthetic process measurements.",
    ),
    DatasetVersion(
        version="2.0.0",
        row_count=2_500,
        random_seed_offset=1_000,
        description="More samples with adjusted equipment effects and noise.",
    ),
)


def generate_dataset(
    definition: DatasetVersion,
    output_dir: Path,
    base_seed: int,
) -> GeneratedDataset:
    rng = np.random.default_rng(base_seed + definition.random_seed_offset)
    size = definition.row_count

    equipment = rng.choice(("EQ-01", "EQ-02", "EQ-03", "EQ-04"), size=size)
    process_step = rng.choice(("ETCH", "DEPOSITION", "CLEAN"), size=size)
    temperature = rng.normal(450.0, 18.0, size)
    pressure = rng.normal(100.0, 11.0, size)
    process_time = rng.normal(60.0, 8.0, size)
    gas_flow = rng.normal(50.0, 6.0, size)
    sensor_1 = 0.035 * (temperature - 450.0) + rng.normal(0.0, 0.8, size)
    sensor_2 = 0.045 * (pressure - 100.0) + rng.normal(0.0, 0.9, size)
    inspection = rng.normal(10.0, 1.2, size)

    temperature_risk = np.abs(temperature - 450.0) / 12.0
    interaction_risk = np.maximum(
        0.0,
        ((pressure - 100.0) * (process_time - 60.0)) / 85.0,
    )
    equipment_risk = np.where(equipment == "EQ-04", 0.9, 0.0)
    sensor_risk = np.maximum(0.0, np.abs(sensor_1) - 0.8) * 0.75
    inspection_risk = np.maximum(0.0, inspection - 10.7) * 0.65
    version_noise = 0.72 if definition.version == "1.0.0" else 0.62
    risk = (
        temperature_risk
        + interaction_risk
        + equipment_risk
        + sensor_risk
        + inspection_risk
        + rng.normal(0.0, version_noise, size)
    )
    threshold = np.quantile(risk, 0.62)
    targets = np.where(risk >= threshold, "fail", "pass")

    features = np.column_stack(
        (
            temperature,
            pressure,
            process_time,
            gas_flow,
            sensor_1,
            sensor_2,
            inspection,
            equipment,
            process_step,
        )
    )

    version_dir = output_dir / f"v{definition.version}"
    version_dir.mkdir(parents=True, exist_ok=True)
    csv_path = version_dir / "semiconductor_quality.csv"
    _write_csv(csv_path, features, targets)

    return GeneratedDataset(
        definition=definition,
        csv_path=csv_path,
        features=features,
        targets=targets,
    )


def _write_csv(path: Path, features: np.ndarray, targets: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(CSV_HEADERS)
        for index, (feature_row, target) in enumerate(zip(features, targets, strict=True), start=1):
            writer.writerow(
                (
                    f"SAMPLE-{index:05d}",
                    feature_row[7],
                    feature_row[8],
                    *(f"{float(value):.5f}" for value in feature_row[:7]),
                    target,
                )
            )

