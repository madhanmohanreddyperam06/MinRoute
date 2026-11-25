"""Unit tests for GeocodingService including regression checks for partial cache bugs."""

from backend.services.geocoding_service import GeocodingService


def test_direct_coordinate_parsing():
    service = GeocodingService()
    res = service.geocode_address("13.0824, 80.2759")
    assert res.success is True
    assert res.latitude == 13.0824
    assert res.longitude == 80.2759
    assert res.source == "coordinates"

    invalid = service.parse_direct_coordinates("95.0, 200.0")
    assert invalid is None


def test_fallback_cache_longest_whole_word_matching():
    # Regression test: "Chennai Airport" must NOT match "Chennai" first
    airport_match = GeocodingService.lookup_fallback_cache("Chennai Airport")
    assert airport_match is not None
    assert airport_match[0] == "chennai airport"
    assert airport_match[1] == GeocodingService.FALLBACK_COORDINATES["chennai airport"]

    # Regression test: short generic token "port" must NOT falsely match "chennai port"
    port_only = GeocodingService.lookup_fallback_cache("Port Blair")
    assert port_only is None

    # Regression test: "nagar" alone must NOT falsely match "t nagar" or "anna nagar"
    nagar_only = GeocodingService.lookup_fallback_cache("Indira Nagar")
    assert nagar_only is None


def test_geocode_uses_nominatim_then_photon_then_fallback(monkeypatch):
    service = GeocodingService()

    # Simulate Nominatim + Photon both returning None -> falls back to verified fallback cache
    monkeypatch.setattr(service, "_query_nominatim", lambda addr: None)
    monkeypatch.setattr(service, "_query_photon", lambda addr: None)

    res = service.geocode_address("T Nagar, Chennai", use_cache=True)
    assert res.success is True
    assert res.source == "fallback_cache"
    assert res.latitude == GeocodingService.FALLBACK_COORDINATES["t nagar"][0]

    # Unknown address when offline fails gracefully with clear error
    unknown = service.geocode_address("Nonexistent Imaginary Street 99999", use_cache=False)
    assert unknown.success is False
    assert unknown.error is not None
