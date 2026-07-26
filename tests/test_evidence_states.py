from mexicosint.main import ScanResult, run_consensus


def classify(**fields):
    result = ScanResult(**fields)
    run_consensus(result)
    return result


def test_evidence_state_no_usable_locality():
    result = classify()

    assert result.evidence_state == "no usable locality"
    assert result.consensus_city == ""
    assert result.consensus_sources == []


def test_evidence_state_single_source_result():
    result = classify(region_phonenumbers="Tijuana")

    assert result.evidence_state == "single-source result"
    assert result.consensus_city == "Tijuana"
    assert result.consensus_sources == ["phonenumbers"]


def test_evidence_state_strong_agreement():
    result = classify(region_phonenumbers="Tijuana", abstract_location="Tijuana")

    assert result.evidence_state == "strong agreement"
    assert result.consensus_city == "Tijuana"
    assert result.consensus_sources == ["phonenumbers", "AbstractAPI"]


def test_evidence_state_partial_agreement():
    result = classify(
        region_phonenumbers="Tijuana",
        abstract_location="Tijuana",
        numverify_location="Monterrey",
    )

    assert result.evidence_state == "partial agreement"
    assert result.consensus_city == "Tijuana"
    assert result.consensus_sources == ["phonenumbers", "AbstractAPI"]


def test_evidence_state_conflicting_sources():
    result = classify(region_phonenumbers="Tijuana", abstract_location="Monterrey")

    assert result.evidence_state == "conflicting sources"
    assert result.consensus_city in {"Tijuana", "Monterrey"}
    assert sorted(result.consensus_sources) == ["AbstractAPI", "phonenumbers"]
