"""Report and map persistence for MeXiCOSINT scans."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

from mexicosint.core.scan_result import ScanResult
from mexicosint.core.settings import ScanSettings


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def generate_map(
    result: ScanResult, settings: ScanSettings | None = None
) -> str:
    if not result.latitude or not result.longitude:
        return ""
    settings = settings or ScanSettings()
    try:
        import folium

        settings.ensure_output_dirs()
        map_obj = folium.Map(
            location=[result.latitude, result.longitude],
            zoom_start=13,
        )
        folium.Marker(
            [result.latitude, result.longitude],
            popup=f"{result.e164}<br>{result.consensus_city}",
            tooltip="Centro aproximado de la localidad",
        ).add_to(map_obj)
        folium.Circle(
            [result.latitude, result.longitude],
            radius=5000,
            popup="Area aproximada",
            color="red",
            fill=True,
            fill_opacity=0.1,
        ).add_to(map_obj)
        safe_num = re.sub(r"[^0-9]", "", result.e164)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = settings.map_dir / f"mexicosint_map_{safe_num}_{timestamp}.html"
        map_obj.save(str(path))
        return str(path)
    except Exception as exc:
        result.errors.append(f"Map generation: {exc}")
        return ""


def save_report(
    result: ScanResult, settings: ScanSettings | None = None
) -> str:
    settings = settings or ScanSettings()
    try:
        settings.ensure_output_dirs()
        safe_num = re.sub(r"[^0-9]", "", result.e164) or "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = settings.report_dir / (
            f"mexicosint_report_{safe_num}_{timestamp}.json"
        )
        data = result.to_report_dict()
        data["scan_end_time"] = _now_utc()
        raw = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
        result.report_hash = _sha256(raw)
        data["report_sha256"] = result.report_hash
        with path.open("w", encoding="utf-8") as handle:
            json.dump(
                data,
                handle,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        return str(path)
    except Exception as exc:
        result.errors.append(f"Report generation: {exc}")
        return ""
