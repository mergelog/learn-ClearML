from __future__ import annotations

import sys
from urllib.error import HTTPError, URLError

from .clearml_gateway import ClearmlGateway
from .config import Settings
from .dataset_seeding import seed_datasets
from .server_health import ensure_server_is_ready


def main() -> int:
    try:
        settings = Settings.from_environment()
        ensure_server_is_ready(settings.api_host)
        gateway = ClearmlGateway(settings)
        datasets, _ = seed_datasets(settings, gateway)
        versions = ", ".join(datasets)
        print(
            "Semiconductor datasets ready: "
            f"versions={versions}, output={settings.output_dir}"
        )
        return 0
    except (HTTPError, URLError, OSError, RuntimeError, ValueError) as error:
        print(f"Semiconductor dataset seed failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
