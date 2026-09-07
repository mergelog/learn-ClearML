from __future__ import annotations

import sys
from urllib.error import HTTPError, URLError

from clearml.backend_api.session.defs import MissingConfigError

from tools.clearml_data_status.gateway import fetch_status
from tools.clearml_data_status.report import render_status


def main() -> int:
    try:
        print(render_status(fetch_status()))
        return 0
    except (HTTPError, URLError, MissingConfigError, OSError, RuntimeError, ValueError) as error:
        print(f"ClearML Serverデータ状態の取得に失敗しました: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
