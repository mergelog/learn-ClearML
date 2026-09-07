from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    api_host: str
    web_host: str
    files_host: str
    access_key: str | None = field(repr=False)
    secret_key: str | None = field(repr=False)
    output_dir: Path
    random_seed: int

    @classmethod
    def from_environment(cls) -> "Settings":
        settings = cls(
            api_host=os.getenv("CLEARML_API_HOST", "http://localhost:8008").rstrip("/"),
            web_host=os.getenv("CLEARML_WEB_HOST", "http://localhost:8080").rstrip("/"),
            files_host=os.getenv("CLEARML_FILES_HOST", "http://localhost:8081").rstrip("/"),
            access_key=_optional_environment_value("CLEARML_API_ACCESS_KEY"),
            secret_key=_optional_environment_value("CLEARML_API_SECRET_KEY"),
            output_dir=Path(os.getenv("SEMICONDUCTOR_SEED_OUTPUT", ".generated/semiconductor")),
            random_seed=int(os.getenv("SEMICONDUCTOR_RANDOM_SEED", "20260904")),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if (self.access_key is None) != (self.secret_key is None):
            raise ValueError(
                "CLEARML_API_ACCESS_KEY and CLEARML_API_SECRET_KEY must be set together"
            )


def _optional_environment_value(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


PROJECT_ROOT = "Semiconductor Quality Prediction"
DATASET_NAME = "semiconductor-quality-data"
SEED_TAG = "generated-by-semiconductor-seed-v1"
