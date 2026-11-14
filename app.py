"""Dilekçiler Software — üç projeli Flask Liquid Glass kataloğu."""
from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, request, stream_with_context, url_for
from download_proxy import DownloadError, open_release_stream, suggested_filename
from link_utils import validate_download_link

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "data" / "projects.json"
app = Flask(__name__)
app.json.ensure_ascii = False


def load_catalog():
    with CATALOG.open("r", encoding="utf-8") as handle:
        projects = json.load(handle)
    if not isinstance(projects, list):
        raise ValueError("data/projects.json bir liste olmalı")
    return [p for p in projects if p.get("visible", True)]


def public_projects():
    """Dış kaynak bağlantısı tarayıcıya, HTML'e veya API'ye gönderilmez."""
    projects = load_catalog()
    for project in projects:
        verified = []
        for release in project.get("releases", []):
            try:
                remote = validate_download_link(release.get("url", ""))
                if not remote.startswith("https://github.com/"):
                    continue  # doğrudan dosyayı aktaramayan paylaşım sayfalarını gösterme
                suggested_filename(remote)
            except (ValueError, TypeError, DownloadError):
                continue
            release_id = str(release.get("id", ""))
            if not release_id:
                continue
            verified.append({
                "id": release_id,
                "version": release.get("version", ""),
                "notes": release.get("notes", ""),
                "created_at": release.get("created_at", ""),
                "download_url": url_for("download_file", slug=project["slug"], release_id=release_id),
            })
        project["releases"] = sorted(verified, key=lambda r: r["created_at"], reverse=True)
        project["has_release"] = bool(project["releases"])
    return projects


@app.get("/")
def home():
    projects = public_projects()
    categories = ["Tümü"] + sorted({p.get("category", "Diğer") for p in projects})
    releases = sorted(
        [(p, r) for p in projects for r in p["releases"]],
        key=lambda item: item[1].get("created_at", ""), reverse=True
    )[:4]
    return render_template("index.html", projects=projects, categories=categories, latest=releases)


@app.get("/api/projects")
def catalog_api():
    response = jsonify(public_projects())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/indir/<slug>/<release_id>")
def download_file(slug, release_id):
    """Dosyayı Flask üzerinden akıtır; kullanıcı dış siteye yönlendirilmez."""
    release = next((r for p in load_catalog() if p.get("slug") == slug
                    for r in p.get("releases", []) if str(r.get("id", "")) == release_id), None)
    if release is None:
        abort(404)
    try:
        url = validate_download_link(release.get("url", ""))
        filename = suggested_filename(url)
        if request.method == "HEAD":
            return Response(status=200, headers={
                "Content-Type": "application/octet-stream",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-store, no-transform",
            })
        upstream = open_release_stream(url, range_header=request.headers.get("Range"))
    except (ValueError, TypeError, DownloadError):
        abort(502, description="İndirme dosyasına şu anda ulaşılamıyor.")

    response = Response(stream_with_context(upstream.chunks()), status=upstream.status)
    response.headers["Content-Type"] = "application/octet-stream"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Cache-Control"] = "no-store, no-transform"
    response.headers.update(upstream.headers)
    return response


@app.get("/health")
def health():
    return jsonify({"status": "ok", "projects": len(public_projects())})


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; "
        "script-src 'self'; font-src 'self'; connect-src 'self'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    return response


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5080"))
    print(f"\nDilekçiler Software: http://{host}:{port}\n")
    app.run(host=host, port=port, debug=False)
