"""Protect the three branches of routes.route"""

from femuralabs.toolkit.service.routes import route

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

def test_info_reads_report_when_folder_is_set(tmp_path, monkeypatch):
    """REPORT_FOLDER + info.json -> /info returns that file's body."""
    (tmp_path / "info.json").write_text(
        '{"shape": [9, 9, 9], "from": "file", "extent_mm": [9.0, 9.0, 9.0]}'
    )
    monkeypatch.setenv("REPORT_FOLDER", str(tmp_path))
    code, body = route("/info")
    assert code == 200
    assert body["from"] == "file"
    assert body["shape"] == [9, 9, 9]

def test_info_falls_back_when_no_report(tmp_path, monkeypatch):
    """REPORT_FOLDER set but folder empty -> /info falls back to geometry."""
    monkeypatch.setenv("REPORT_FOLDER", str(tmp_path))
    code, body = route("/info")
    assert code == 200
    assert body["shape"] == [4, 6, 6]
    assert "extent_mm" in body