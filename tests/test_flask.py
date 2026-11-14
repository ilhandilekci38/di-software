"""Flask uçları: dış indirme adresinin istemciye sızmadığını denetle."""
import pytest
from pathlib import Path
from io import BytesIO

pytest.importorskip("flask")
import app as module
from download_proxy import Upstream, DownloadError


def test_public_catalog_and_markup_hide_origin():
    module.CATALOG = Path(__file__).resolve().parents[1] / "data" / "projects.json"
    client = module.app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/health").json["projects"] == 3
    response = client.get("/api/projects")
    data = response.json
    assert {p["slug"] for p in data} == {"atoai-27", "di-browser", "pydi-ide"}
    assert all(len(p["releases"]) == 1 for p in data)
    for p in data:
        release = p["releases"][0]
        assert release["download_url"].startswith(f'/indir/{p["slug"]}/')
        assert "host_name" not in release
        assert "url" not in release
    for body in (response.get_data(as_text=True), client.get("/").get_data(as_text=True)):
        assert "github.com" not in body.lower()
        assert "GitHub" not in body
        assert "dosya.co" not in body.lower()
    assert "github.com" not in (Path(__file__).resolve().parents[1] / "static/js/app.js").read_text()


def test_download_is_streamed_under_own_hostname(monkeypatch):
    module.CATALOG = Path(__file__).resolve().parents[1] / "data" / "projects.json"
    requested = []

    def fake_stream(url, range_header=None):
        requested.append((url, range_header))
        return Upstream(BytesIO(b"MZsample"), 200, {"Content-Length": "8"})

    monkeypatch.setattr(module, "open_release_stream", fake_stream)
    client = module.app.test_client()
    response = client.get("/indir/atoai-27/surum-27")
    assert response.status_code == 200
    assert response.data == b"MZsample"
    assert response.headers["Content-Disposition"] == 'attachment; filename="di-ato.27.exe"'
    assert response.headers["Content-Type"] == "application/octet-stream"
    assert "Location" not in response.headers
    assert "github.com" not in str(dict(response.headers)).lower()
    assert len(requested) == 1


def test_range_and_failures(monkeypatch):
    module.CATALOG = Path(__file__).resolve().parents[1] / "data" / "projects.json"

    def fake_stream(url, range_header=None):
        assert range_header == "bytes=2-"
        return Upstream(BytesIO(b"sample"), 206, {"Content-Range": "bytes 2-7/8", "Accept-Ranges": "bytes"})

    monkeypatch.setattr(module, "open_release_stream", fake_stream)
    response = module.app.test_client().get("/indir/di-browser/surum-27", headers={"Range": "bytes=2-"})
    assert response.status_code == 206
    assert response.data == b"sample"
    assert response.headers["Content-Range"] == "bytes 2-7/8"

    assert module.app.test_client().get("/indir/olmayani/surum-27").status_code == 404
    monkeypatch.setattr(module, "open_release_stream", lambda *a, **kw: (_ for _ in ()).throw(DownloadError("bad")))
    assert module.app.test_client().get("/indir/di-browser/surum-27").status_code == 502
