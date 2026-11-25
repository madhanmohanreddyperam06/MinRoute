"""Unit tests for RoadRoutingService OSRM URL formatting, GeoJSON parsing, and caching."""

from unittest.mock import Mock

from backend.services.road_routing_service import RoadRoutingService


def test_road_routing_osrm_geojson_and_cache(monkeypatch):
    service = RoadRoutingService()
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params))
        resp = Mock()
        resp.status_code = 200
        resp.json.return_value = {
            "code": "Ok",
            "routes": [
                {
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[80.2759, 13.0824], [80.2500, 13.0600], [80.2337, 13.0418]],
                    }
                }
            ],
        }
        return resp

    monkeypatch.setattr("backend.services.road_routing_service.requests.get", fake_get)

    pts, is_road = service.get_route_geometry((13.0824, 80.2759), (13.0418, 80.2337))
    assert is_road is True
    assert pts == [(13.0824, 80.2759), (13.06, 80.25), (13.0418, 80.2337)]
    assert "80.2759,13.0824;80.2337,13.0418" in calls[0][0]

    # Second identical call hits LRU cache instead of calling OSRM again
    pts2, is_road2 = service.get_route_geometry((13.0824, 80.2759), (13.0418, 80.2337))
    assert is_road2 is True
    assert pts2 == pts
    assert len(calls) == 1


def test_road_routing_graceful_fallback_on_error(monkeypatch):
    service = RoadRoutingService()

    def fail_get(*args, **kwargs):
        raise TimeoutError("network timeout")

    monkeypatch.setattr("backend.services.road_routing_service.requests.get", fail_get)

    pts, is_road = service.get_route_geometry((13.0824, 80.2759), (13.0418, 80.2337))
    assert is_road is False
    assert pts == [(13.0824, 80.2759), (13.0418, 80.2337)]


def test_multi_leg_geometries_single_call_and_cache(monkeypatch):
    service = RoadRoutingService()
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append(url)
        resp = Mock()
        resp.status_code = 200
        resp.json.return_value = {
            "code": "Ok",
            "routes": [
                {
                    "legs": [
                        {
                            "steps": [
                                {"geometry": {"coordinates": [[80.2759, 13.0824], [80.25, 13.06]]}},
                                {"geometry": {"coordinates": [[80.25, 13.06], [80.2337, 13.0418]]}},
                            ]
                        },
                        {
                            "steps": [
                                {"geometry": {"coordinates": [[80.2337, 13.0418], [80.2565, 13.0012]]}},
                            ]
                        },
                    ]
                }
            ],
        }
        return resp

    monkeypatch.setattr("backend.services.road_routing_service.requests.get", fake_get)

    waypoints = [(13.0824, 80.2759), (13.0418, 80.2337), (13.0012, 80.2565)]
    res = service.get_multi_leg_geometries(waypoints, use_road_network=True)
    assert len(calls) == 1
    assert len(res) == 2
    assert res[0][1] is True
    assert res[0][0] == [(13.0824, 80.2759), (13.06, 80.25), (13.0418, 80.2337)]
    assert res[1][0] == [(13.0418, 80.2337), (13.0012, 80.2565)]

    # Second call should serve entirely from cache (0 extra HTTP calls)
    res2 = service.get_multi_leg_geometries(waypoints, use_road_network=True)
    assert len(calls) == 1
    assert res2 == res
