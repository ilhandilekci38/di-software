"""Dilekçiler Software — Flask / Liquid Glass / dosya.co linkli yazılım kataloğu."""
from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template
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
    projects = load_catalog()
    for project in projects:
        verified = []
        for release in project.get("releases", []):
            try:
                link = validate_download_link(release.get("url", ""))
            except (ValueError, TypeError):
                continue
            verified.append({
                "id": release.get("id", ""),
                "version": release.get("version", ""),
                "notes": release.get("notes", ""),
                "created_at": release.get("created_at", ""),
                "download_url": link,
                "host_name": "dosya.co",
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
