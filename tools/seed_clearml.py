#!/usr/bin/env python3
"""Create a tiny, idempotent dataset for local stackup development."""

from __future__ import annotations

import json
import os
import sys
import time
from base64 import b64encode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


API_HOST = os.getenv("CLEARML_API_HOST", "http://localhost:8008").rstrip("/")
PROJECT_NAME = "stackup/test"


def get_credentials() -> tuple[str, str] | None:
    access_key = os.getenv("CLEARML_API_ACCESS_KEY", "").strip()
    secret_key = os.getenv("CLEARML_API_SECRET_KEY", "").strip()
    if bool(access_key) != bool(secret_key):
        raise RuntimeError(
            "CLEARML_API_ACCESS_KEY and CLEARML_API_SECRET_KEY must be set together"
        )
    return (access_key, secret_key) if access_key else None


def call(endpoint: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    credentials = get_credentials()
    if credentials is not None:
        access_key, secret_key = credentials
        encoded_credentials = b64encode(f"{access_key}:{secret_key}".encode()).decode()
        headers["Authorization"] = f"Basic {encoded_credentials}"
    request = Request(
        f"{API_HOST}/{endpoint}",
        data=data,
        headers=headers,
        method="GET" if data is None else "POST",
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def wait_until_ready() -> None:
    for _ in range(60):
        try:
            call("debug.ping")
            return
        except (HTTPError, OSError, TimeoutError):
            time.sleep(2)
    raise RuntimeError(f"ClearML API did not become ready at {API_HOST}")


def find_project() -> str | None:
    result = call("projects.get_all", {"name": PROJECT_NAME, "only_fields": ["id", "name"]})
    projects = result.get("data", {}).get("projects", [])
    return next((project["id"] for project in projects if project.get("name") == PROJECT_NAME), None)


def ensure_project() -> str:
    project_id = find_project()
    if project_id:
        return project_id
    result = call(
        "projects.create",
        {"name": PROJECT_NAME, "description": "Minimal local development data for stackup."},
    )
    return result["data"]["id"]


def ensure_task(project_id: str) -> str:
    task_name = "hello-stackup"
    result = call(
        "tasks.get_all",
        {"project": [project_id], "name": task_name, "only_fields": ["id", "name"]},
    )
    tasks = result.get("data", {}).get("tasks", [])
    if tasks:
        return tasks[0]["id"]
    created = call(
        "tasks.create",
        {
            "name": task_name,
            "project": project_id,
            "type": "testing",
            "comment": "Seed task for Angular and API smoke testing.",
        },
    )
    return created["data"]["id"]


def main() -> int:
    try:
        wait_until_ready()
        project_id = ensure_project()
        task_id = ensure_task(project_id)
    except (HTTPError, OSError, KeyError, RuntimeError) as error:
        print(f"Seed failed: {error}", file=sys.stderr)
        return 1
    print(f"Seed ready: project={PROJECT_NAME} ({project_id}), task={task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
