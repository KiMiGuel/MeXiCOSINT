import json
from pathlib import Path

import requests

import mexicosint.main as app
from mexicosint.core.scan_result import ScanResult
from mexicosint.providers.status import (
    ProviderRequestError,
    ProviderState,
    ProviderStatus,
    classify_provider_exception,
)


def test_configured_credentials_start_unverified_without_validation(monkeypatch):
    monkeypatch.setattr(
        "mexicosint.config.get_credential_source",
        lambda service, config=None, dummy_mode=False: "microvault",
    )
    result = ScanResult()

    app._initialize_provider_states(
        result,
        {"geoapify": "configured"},
        ["geoapify"],
        app.ScanSettings(),
    )

    assert result.provider_states["geoapify"].state == (
        ProviderState.CONFIGURED_UNVERIFIED
    )
    assert result.provider_states["geoapify"].source == "microvault"
    assert result.provider_states["geoapify"].request_attempted is False
    assert result.provider_states["opencage"].state == ProviderState.MISSING


def test_dummy_scan_serializes_structured_provider_states(monkeypatch, tmp_path):
    settings = app.ScanSettings(dummy_mode=True, output_dir=tmp_path)
    config = app.init_config(settings=settings)

    result = app.run_phone_scan(
        "5512345678",
        config,
        list(app.SAMPLE_CONFIG),
        settings,
    )

    assert result.provider_states["abstract_phone_intelligence"].state == (
        ProviderState.REQUEST_SUCCESS
    )
    assert result.provider_states["abstract_phone_intelligence"].transport == (
        "fixture"
    )
    assert result.provider_states["nominatim"].state == ProviderState.NOT_REQUESTED
    assert result.geocoding_source == "fixture"
    assert result.local_line_type == "CELULAR PROBABLE"

    report = json.loads(Path(result.report_path).read_text(encoding="utf-8"))
    assert report["provider_states"]["numverify"]["state"] == "request_success"
    assert report["provider_states"]["numverify"]["transport"] == "fixture"
    assert report["geocoding_source"] == "fixture"
    assert report["provider_states"]["nominatim"]["state"] == "not_requested"
    assert report["local_line_type"] == "CELULAR PROBABLE"


def test_provider_exception_classification():
    assert classify_provider_exception(
        ProviderRequestError(ProviderState.AUTH_FAILED, "denied", http_status=401)
    ).state == ProviderState.AUTH_FAILED
    assert classify_provider_exception(
        ProviderRequestError(
            ProviderState.QUOTA_EXCEEDED,
            "limit reached",
            http_status=429,
        )
    ).state == ProviderState.QUOTA_EXCEEDED
    assert classify_provider_exception(
        ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "unsupported payload",
            http_status=200,
        )
    ).state == ProviderState.INVALID_RESPONSE


def test_http_error_status_is_classified_and_redacted():
    key = "secret-provider-key"
    response = requests.Response()
    response.status_code = 401
    response.url = f"https://example.test/?api_key={key}"
    exc = requests.HTTPError("401 denied", response=response)

    status = app._provider_error_status(exc, key)

    assert status.state == ProviderState.AUTH_FAILED
    assert status.http_status == 401
    assert key not in status.detail


def test_plain_provider_state_output_contains_no_credential_material(capsys):
    result = ScanResult()
    result.provider_states["geoapify"] = ProviderStatus(
        state=ProviderState.AUTH_FAILED,
        source="microvault",
        transport="live_request",
        request_attempted=True,
        http_status=401,
        detail="request rejected",
    )

    app.plain_print_provider_states(result)
    output = capsys.readouterr().out

    assert "Geoapify" in output
    assert "auth_failed" in output
    assert "microvault" in output
    assert "API_KEY" not in output


def test_presentation_functions_remain_reexported_from_main():
    from mexicosint import presentation
    from mexicosint.services import scanner

    assert app.print_results is presentation.print_results
    assert scanner.print_results is presentation.print_results
    assert app.plain_print_provider_states is presentation.plain_print_provider_states
