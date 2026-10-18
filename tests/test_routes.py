"""Protect the three branches of routes.route"""

from femuralabs.toolkit.routes import route

def test_health_route():
	assert route("/health") == (200, {"status": "ok"})

def test_info_route_returns_geometry():
	code, body = route("/info")
	assert code == 200
	assert body["shape"] == [4, 6, 6]
	assert body["spacing"] == [2.0, 1.0, 1.0]
	assert body["dtype"] == "float32"
	assert body["extent_mm"] == [8.0, 6.0, 6.0]

def test_unknown_route_is_404():
	code, body = route("/nope")
	assert code == 404
	assert body == {"error": "not found"}


