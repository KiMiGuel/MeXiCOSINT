"""Report and map persistence for MeXiCOSINT scans."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from mexicosint.core.scan_result import ScanResult
from mexicosint.core.settings import ScanSettings
from mexicosint.history import record_scan


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
            popup=(
                f"{result.e164}<br>{result.consensus_city}<br>"
                f"Localidad de numeracion; precision aproximada "
                f"(~{result.location_accuracy_km:.0f} km)"
            ),
            tooltip="Centro aproximado de localidad; no ubicacion del suscriptor",
        ).add_to(map_obj)
        folium.Circle(
            [result.latitude, result.longitude],
            radius=max(5000, min(result.location_accuracy_km * 1000, 100000)),
            popup=(
                "Area aproximada de la localidad de numeracion; "
                "no es una ubicacion GPS"
            ),
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
        try:
            record_scan(result, settings)
        except Exception as exc:
            result.errors.append(f"History update: {exc}")
        return str(path)
    except Exception as exc:
        result.errors.append(f"Report generation: {exc}")
        return ""


def save_batch_exports(
    results: list[ScanResult],
    source_name: str,
    settings: ScanSettings | None = None,
) -> tuple[str, str]:
    """Write a batch JSON manifest and a compact CSV summary."""
    settings = settings or ScanSettings()
    settings.ensure_output_dirs()
    batch_dir = settings.output_dir / "batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    source_stem = Path(source_name).stem
    safe_source = re.sub(r"[^A-Za-z0-9_.-]+", "_", source_stem).strip("_") or "batch"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = batch_dir / f"mexicosint_batch_{safe_source}_{timestamp}"
    manifest_path = base.with_suffix(".json")
    csv_path = base.with_suffix(".csv")

    manifest = {
        "schema_version": "2.9",
        "source": source_name,
        "scan_count": len(results),
        "scans": [
            {
                "scan_id": result.scan_id,
                "e164": result.e164,
                "valid": result.valid,
                "ift_carrier": result.ift_carrier,
                "locality": result.consensus_city,
                "latitude": result.latitude,
                "longitude": result.longitude,
                "report_path": result.report_path,
                "map_path": result.map_path,
                "provider_health": result.mexico_data_trust.get("provider_health", {}),
            }
            for result in results
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "scan_id",
                "e164",
                "valid",
                "ift_carrier",
                "locality",
                "latitude",
                "longitude",
                "report_path",
                "map_path",
            ],
        )
        writer.writeheader()
        for item in manifest["scans"]:
            writer.writerow({field: item.get(field, "") for field in writer.fieldnames})
    return str(manifest_path), str(csv_path)
