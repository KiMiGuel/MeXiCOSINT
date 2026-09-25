"""Canonical result model for a MeXiCOSINT phone scan."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from mexicosint.core.models import (
    ApiResponse,
    ConsensusResult,
    GeocodingResult,
    IftBlockInfo,
    PhoneInfo,
    ReputationResult,
)
from mexicosint.evidence import EvidenceState
from mexicosint.providers.status import ProviderState, ProviderStatus


REPORT_SCHEMA_VERSION = "2.9"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@dataclass
class ScanResult:
    scan_id: str = ""
    raw_input: str = ""
    detected_format: str = ""
    international_digits: str = ""
    is_possible: bool = False
    is_mexican: bool = False
    e164: str = ""
    valid: bool = False
    country_code: str = ""
    national_number: str = ""
    region_phonenumbers: str = ""
    lada_region: str = ""
    ift_carrier: str = ""
    ift_modality: str = ""
    ift_zona: str = ""
    ift_fecha_asignacion: str = ""
    ift_service_type: str = ""
    canonical_locality_city: str = ""
    canonical_locality_state: str = ""
    canonical_locality_query: str = ""
    canonical_locality_source: str = ""
    abstract_data: dict = field(default_factory=dict)
    numverify_data: dict = field(default_factory=dict)
    abstract_location: str = ""
    numverify_location: str = ""
    abstract_carrier: str = ""
    numverify_carrier: str = ""
    abstract_line_type: str = ""
    numverify_line_type: str = ""
    local_line_type: str = ""
    consensus_city: str = ""
    consensus_confidence: float = 0.0
    consensus_sources: list = field(default_factory=list)
    evidence_state: EvidenceState = EvidenceState.NO_USABLE_LOCALITY
    all_votes: list = field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    nominatim_address: str = ""
    opencage_data: dict = field(default_factory=dict)
    opencage_latitude: float | None = None
    opencage_longitude: float | None = None
    opencage_address: str = ""
    geoapify_data: dict = field(default_factory=dict)
    geoapify_latitude: float | None = None
    geoapify_longitude: float | None = None
    geoapify_address: str = ""
    ipqualityscore_data: dict = field(default_factory=dict)
    provider_trace: list = field(default_factory=list)
    provider_states: dict[str, ProviderStatus] = field(default_factory=dict)
    geocoding_source: str = ""
    osint_links: dict = field(default_factory=dict)
    map_path: str = ""
    report_path: str = ""
    report_hash: str = ""
    errors: list = field(default_factory=list)
    mexico_data_trust: dict = field(default_factory=dict)
    location_precision: str = "numbering_locality"
    location_accuracy_km: float = 25.0
    scan_timestamp: str = field(default_factory=utc_timestamp)

    @property
    def phone(self) -> PhoneInfo:
        return PhoneInfo(
            raw_input=self.raw_input,
            detected_format=self.detected_format,
            international_digits=self.international_digits,
            is_possible=self.is_possible,
            is_mexican=self.is_mexican,
            e164=self.e164,
            valid=self.valid,
            country_code=self.country_code,
            national_number=self.national_number,
            region_phonenumbers=self.region_phonenumbers,
            lada_region=self.lada_region,
        )

    @property
    def ift_block(self) -> IftBlockInfo:
        return IftBlockInfo(
            carrier=self.ift_carrier,
            modality=self.ift_modality,
            zona=self.ift_zona,
            fecha_asignacion=self.ift_fecha_asignacion,
            service_type=self.ift_service_type,
        )

    @property
    def abstract(self) -> ApiResponse:
        return ApiResponse(
            provider="AbstractAPI",
            raw=self.abstract_data,
            location=self.abstract_location,
            carrier=self.abstract_carrier,
            line_type=self.abstract_line_type,
        )

    @property
    def numverify(self) -> ApiResponse:
        return ApiResponse(
            provider="NumVerify",
            raw=self.numverify_data,
            location=self.numverify_location,
            carrier=self.numverify_carrier,
            line_type=self.numverify_line_type,
        )

    @property
    def opencage(self) -> GeocodingResult:
        return GeocodingResult(
            provider="OpenCage",
            raw=self.opencage_data,
            latitude=self.opencage_latitude,
            longitude=self.opencage_longitude,
            address=self.opencage_address,
        )

    @property
    def geoapify(self) -> GeocodingResult:
        return GeocodingResult(
            provider="Geoapify",
            raw=self.geoapify_data,
            latitude=self.geoapify_latitude,
            longitude=self.geoapify_longitude,
            address=self.geoapify_address,
        )

    @property
    def ipqualityscore(self) -> ReputationResult:
        return ReputationResult(
            provider="IPQualityScore",
            raw=self.ipqualityscore_data,
        )

    @property
    def consensus(self) -> ConsensusResult:
        return ConsensusResult(
            state=self.evidence_state,
            city=self.consensus_city,
            confidence=self.consensus_confidence,
            sources=self.consensus_sources,
            all_votes=self.all_votes,
        )

    def _provider_health(self) -> dict:
        counts: dict[str, int] = {}
        for status in self.provider_states.values():
            state = str(status.state)
            counts[state] = counts.get(state, 0) + 1
        return {
            "total": len(self.provider_states),
            "by_state": counts,
            "successful": counts.get(ProviderState.REQUEST_SUCCESS.value, 0),
            "degraded": sum(
                count
                for state, count in counts.items()
                if state not in {
                    ProviderState.REQUEST_SUCCESS.value,
                    ProviderState.NOT_REQUESTED.value,
                }
            ),
        }

    def finalize_mexico_data_trust(self) -> None:
        """Record which phone fields are Mexico-authoritative vs secondary.

        IFT/PNN is the primary source for Mexican numbering-block facts. External
        APIs may corroborate format, carrier, or line type, but must never
        silently replace the official Mexican block data.
        """
        ift_fields = [
            name
            for name, value in (
                ("carrier", self.ift_carrier),
                ("modality", self.ift_modality),
                ("assignment_date", self.ift_fecha_asignacion),
                ("service_type", self.ift_service_type),
                ("zone", self.ift_zona),
            )
            if value
        ]
        secondary = []
        for provider, data in (
            ("AbstractAPI", self.abstract_data),
            ("NumVerify", self.numverify_data),
            ("IPQualityScore", self.ipqualityscore_data),
        ):
            if not data:
                continue
            available = [
                field
                for field in (
                    "valid",
                    "active",
                    "risk_level",
                    "risk_score",
                    "abuse_recent",
                    "abuse_detected",
                    "is_voip",
                    "is_disposable",
                    "carrier",
                    "line_type",
                    "location",
                    "region",
                )
                if data.get(field) not in (None, "")
            ]
            secondary.append(
                {
                    "provider": provider,
                    "role": "secondary corroboration",
                    "available_fields": available,
                }
            )
        self.location_precision = "numbering_locality"
        if self.consensus_city:
            self.location_accuracy_km = 25.0
        elif self.lada_region:
            self.location_accuracy_km = 50.0
        else:
            self.location_accuracy_km = 100.0
        self.mexico_data_trust = {
            "policy": "Mexico-first",
            "primary_phone_source": "IFT/PNN" if ift_fields else "local parser",
            "primary_fields": ift_fields,
            "secondary_phone_sources": secondary,
            "provider_capabilities": {
                "IFT/PNN": {
                    "role": "primary",
                    "scope": "Mexico numbering blocks",
                    "fields": ["carrier", "modality", "assignment_date", "service_type", "zone"],
                },
                "local_parser": {
                    "role": "local validation",
                    "scope": "Mexican number format and locality hints",
                    "fields": ["format", "possible", "line_type", "locality_hint"],
                },
                "OpenCage/Geoapify/Nominatim": {
                    "role": "locality geocoding",
                    "scope": "approximate locality only",
                    "fields": ["city", "state", "latitude", "longitude"],
                },
                "AbstractAPI/NumVerify/IPQualityScore": {
                    "role": "secondary corroboration",
                    "scope": "external provider metadata",
                    "fields": ["validity", "carrier", "line_type", "risk", "activity"],
                },
            },
            "provider_health": self._provider_health(),
            "external_sources_override_ift": False,
            "locality_is_subscriber_location": False,
            "location_precision": self.location_precision,
            "location_accuracy_km": self.location_accuracy_km,
            "confidence": "high" if ift_fields else "medium",
            "limitations": [
                "IFT/PNN describes the assigned numbering block, not the current subscriber.",
                "External provider data is secondary and may reflect another database.",
                "Geocoding locality is approximate numbering locality, not GPS location.",
            ],
        }

    def to_dict(self) -> dict:
        return asdict(self)

    def to_report_dict(self) -> dict:
        """Return the export payload without internal report path fields."""
        data = self.to_dict()
        data.pop("report_path", None)
        data.pop("report_hash", None)
        data["report_manifest"] = {
            "tool": "MeXiCOSINT",
            "schema_version": REPORT_SCHEMA_VERSION,
            "scan_id": self.scan_id,
            "scan_timestamp": self.scan_timestamp,
            "source_policy": "Mexico-first",
            "primary_phone_source": self.mexico_data_trust.get(
                "primary_phone_source", "local parser"
            ),
            "provider_health": self.mexico_data_trust.get("provider_health", {}),
        }
        return data
