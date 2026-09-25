"""Local scan history and evidence-diff helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mexicosint.core.settings import ScanSettings


HISTORY_FIELDS = (
    "valid",
    "ift_carrier",
    "consensus_city",
    "latitude",
    "longitude",
    "provider_health",
)


def history_path(settings: ScanSettings | None = None) -> Path:
    settings = settings or ScanSettings()
    return settings.output_dir / "history.jsonl"


def _summary(result) -> dict[str, Any]:
    return {
        "scan_id": result.scan_id,
        "e164": result.e164,
        "scan_timestamp": result.scan_timestamp,
        "valid": result.valid,
        "ift_carrier": result.ift_carrier,
        "consensus_city": result.consensus_city,
        "latitude": result.latitude,
        "longitude": result.longitude,
        "provider_health": result.mexico_data_trust.get("provider_health", {}),
        "report_path": result.report_path,
        "map_path": result.map_path,
    }


def record_scan(result, settings: ScanSettings | None = None) -> str:
    settings = settings or ScanSettings()
    path = history_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_summary(result), ensure_ascii=False, default=str) + "\n")
    return str(path)


def load_history(settings: ScanSettings | None = None) -> list[dict[str, Any]]:
    path = history_path(settings)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def diff_scan_summaries(before: dict, after: dict) -> dict[str, dict]:
    """Return changed evidence fields between two scan summaries."""
    changes: dict[str, dict] = {}
    for field in HISTORY_FIELDS:
        old = before.get(field)
        new = after.get(field)
        if old != new:
            changes[field] = {"before": old, "after": new}
    return changes
