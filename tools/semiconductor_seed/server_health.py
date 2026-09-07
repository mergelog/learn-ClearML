from __future__ import annotations

from urllib.request import urlopen


def ensure_server_is_ready(api_host: str) -> None:
    with urlopen(f"{api_host}/debug.ping", timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"ClearML API is not ready at {api_host}")
