from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from tools.clearml_data_status.domain import ClearmlDataStatus, InventoryItem


CATEGORIES = (
    ("Project", "projects"),
    ("Dataset", "datasets"),
    ("Training Task", "training_tasks"),
    ("その他のTask", "other_tasks"),
    ("Model", "models"),
)
DISPLAY_TIMEZONE = ZoneInfo("Asia/Tokyo")


def render_status(status: ClearmlDataStatus) -> str:
    lines = [
        "ClearML Serverデータ状態",
        f"接続先: {status.api_host}",
        f"確認対象: {status.project_root}",
        "",
        "ClearML Server全体:",
        f"- Project: {status.total_projects}件",
        f"- Task: {status.total_tasks}件",
        f"- Model: {status.total_models}件",
        "",
    ]

    for label, attribute_name in CATEGORIES:
        items = getattr(status, attribute_name)
        lines.extend(_render_category(label, items))

    if status.has_learning_data:
        lines.append("判定: 半導体学習データが登録されています。")
    else:
        lines.append("判定: 半導体学習データはありません。学習開始前の状態です。")

    return "\n".join(lines)


def _render_category(label: str, items: tuple[InventoryItem, ...]) -> list[str]:
    lines = [f"[{label}]"]
    if not items:
        lines.extend((f"現在の{label}データはありません。", ""))
        return lines

    lines.append(f"現在の{label}データは{len(items)}件あります。")
    for item in items:
        attributes = ", ".join(f"{key}: {value}" for key, value in item.attributes)
        suffix = f" ({attributes})" if attributes else ""
        lines.append(f"- {item.name}{suffix}")
        lines.append(f"  Project: {item.project}")
        lines.append(f"  ID: {item.item_id}")
        lines.append(f"  作成日時 (Asia/Tokyo): {_format_datetime(item.created_at)}")
    lines.append("")
    return lines


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "不明"
    return value.astimezone(DISPLAY_TIMEZONE).isoformat(timespec="seconds")
