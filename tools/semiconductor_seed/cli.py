from __future__ import annotations

import sys
from urllib.error import HTTPError, URLError

from .clearml_gateway import ClearmlGateway
from .config import Settings
from .dataset_seeding import seed_datasets
from .scenarios import experiment_specs
from .server_health import ensure_server_is_ready
from .training import train_experiment


def main() -> int:
    try:
        settings = Settings.from_environment()
        ensure_server_is_ready(settings.api_host)
        gateway = ClearmlGateway(settings)
        datasets, dataset_ids = seed_datasets(settings, gateway)

        created_count = 0
        skipped_count = 0
        for spec in experiment_specs():
            if gateway.experiment_exists(spec):
                print(f"Experiment exists, skipped: {spec.name}")
                skipped_count += 1
                continue

            result = None
            if spec.model_kind not in {"failure", "aborted"}:
                result = train_experiment(
                    spec,
                    datasets[spec.dataset_version],
                    settings.random_seed,
                )
            task_id = gateway.register_experiment(
                spec,
                dataset_ids[spec.dataset_version],
                result,
                settings.output_dir / "artifacts",
                settings.random_seed,
            )
            print(f"Experiment created: {spec.name} ({task_id})")
            created_count += 1

        print(
            "Semiconductor seed ready: "
            f"created={created_count}, skipped={skipped_count}, "
            f"output={settings.output_dir}"
        )
        return 0
    except (HTTPError, URLError, OSError, RuntimeError, ValueError) as error:
        print(f"Semiconductor seed failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
