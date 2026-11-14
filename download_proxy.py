"""Doğrudan ikili indirme aktarımı; kaynak adres tarayıcıya verilmez.

Yalnızca doğrulanmış GitHub Release ikili dosyaları aktarılır. Bu bileşen
büyük EXE dosyalarını RAM'e almadan parça parça yayınlar.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from link_utils import validate_download_link

# GitHub Release indirmeleri imzalı varlık adreslerine yönlenebilir.
_ALLOWED_ASSET_HOSTS = frozenset({
    "github.com",
    "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
    "github-production-release-asset-2e65be.s3.amazonaws.com",
})
_REDIRECTS = frozenset({301, 302, 303, 307, 308})
_RANGE = re.compile(r"^bytes=(?:\d+-\d*|-\d+)$")
_CHUNK_SIZE = 256 * 1024


class DownloadError(Exception):
    """Upstream bağlantısı başarısız veya güvenilir değil."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


@dataclass
class Upstream:
    response: object
    status: int
    headers: dict[str, str]

    def chunks(self):
        try:
            while True:
                chunk = self.response.read(_CHUNK_SIZE)
                if not chunk:
                    return
                yield chunk
        finally:
            self.response.close()


def suggested_filename(url: str) -> str:
    """GitHub adresindeki dosya adını HTTP başlığı için güvenli tut."""
    raw = urlsplit(url).path.rsplit("/", 1)[-1]
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", raw)[:150]
    if not name.lower().endswith((".exe", ".msi", ".zip", ".apk")):
        raise DownloadError("Yalnızca uygulama dağıtım dosyaları indirilebilir")
    return name


def _validate_asset_url(url: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise DownloadError("Geçersiz yönlendirme") from exc
    if (parsed.scheme != "https" or parsed.hostname not in _ALLOWED_ASSET_HOSTS
            or port not in (None, 443) or parsed.username or parsed.password):
        raise DownloadError("İndirme adresi güvenilir değil")


def _range_value(value: str | None) -> str | None:
    return value if value and len(value) <= 100 and _RANGE.fullmatch(value) else None


def open_release_stream(url: str, range_header: str | None = None, opener=None) -> Upstream:
    """HTTP yönlendirmelerini sunucuda takip edip bayt akışını aç."""
    url = validate_download_link(url)
    if urlsplit(url).hostname != "github.com":
        raise DownloadError("Bu bağlantı doğrudan EXE indirmesini desteklemiyor")
    suggested_filename(url)
    client = opener or build_opener(_NoRedirect())
    headers = {"User-Agent": "di-software-download/27", "Accept": "application/octet-stream"}
    byte_range = _range_value(range_header)
    if byte_range:
        headers["Range"] = byte_range

    for _ in range(7):
        _validate_asset_url(url)
        request = Request(url, headers=headers, method="GET")
        try:
            upstream = client.open(request, timeout=25)
            status = upstream.getcode()
        except HTTPError as exc:
            upstream = exc
            status = exc.code
        except (OSError, ValueError) as exc:
            raise DownloadError("Dosyaya şu anda ulaşılamıyor") from exc

        if status in _REDIRECTS:
            location = upstream.headers.get("Location")
            upstream.close()
            if not location:
                raise DownloadError("İndirme yönlendirmesi geçersiz")
            url = urljoin(url, location)
            _validate_asset_url(url)
            continue

        if status not in (200, 206):
            upstream.close()
            raise DownloadError(f"İndirme sunucusu dosyayı göndermedi ({status})")

        content_type = upstream.headers.get("Content-Type", "").lower().split(";", 1)[0].strip()
        if content_type in {"text/html", "application/json", "text/plain"}:
            upstream.close()
            raise DownloadError("Dosya yerine bir web sayfası döndürüldü")

        output_headers = {}
        for name in ("Content-Length", "Content-Range", "ETag", "Last-Modified"):
            value = upstream.headers.get(name)
            if value:
                output_headers[name] = value
        if upstream.headers.get("Accept-Ranges") == "bytes" or status == 206:
            output_headers["Accept-Ranges"] = "bytes"
        return Upstream(upstream, status, output_headers)

    raise DownloadError("Çok fazla yönlendirme")
