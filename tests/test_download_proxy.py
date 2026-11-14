"""Gerçek ağa bağlanmadan indirme akışını denetle."""
from io import BytesIO
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest
from download_proxy import DownloadError, open_release_stream, suggested_filename

RELEASE = "https://github.com/ilhandilekci38/di-software/releases/download/27/di-ato.27.exe"
ASSET = "https://release-assets.githubusercontent.com/12345/example?token=test"


class Reply(BytesIO):
    def __init__(self, data, status, headers):
        super().__init__(data)
        self.status = status
        self.headers = headers

    def getcode(self):
        return self.status


class RedirectOpener:
    def __init__(self, destination=ASSET, body=b"MZabcdefghijklmnopqrstuvwxyz"):
        self.destination = destination
        self.body = body
        self.urls = []
        self.headers = []

    def open(self, request, timeout=None):
        self.urls.append(request.full_url)
        self.headers.append(dict(request.headers))
        if len(self.urls) == 1:
            raise HTTPError(request.full_url, 302, "Found", {"Location": self.destination}, None)
        return Reply(self.body, 200, {"Content-Type": "application/octet-stream", "Content-Length": str(len(self.body))})


def test_proxy_follows_allowed_redirect_and_streams():
    opener = RedirectOpener()
    result = open_release_stream(RELEASE, opener=opener, range_header="bytes=5-")
    assert result.status == 200
    assert b"".join(result.chunks()) == opener.body
    assert opener.urls == [RELEASE, ASSET]
    assert all(headers.get("Range") == "bytes=5-" for headers in opener.headers)
    assert result.response.closed


def test_reject_malicious_redirect():
    opener = RedirectOpener(destination="http://127.0.0.1/admin")
    with pytest.raises(DownloadError):
        open_release_stream(RELEASE, opener=opener)
    assert len(opener.urls) == 1


def test_reject_invalid_type_and_provider():
    assert suggested_filename(RELEASE) == "di-ato.27.exe"
    with pytest.raises(DownloadError):
        suggested_filename("https://github.com/u/r/releases/download/1/page.html")
    with pytest.raises(DownloadError):
        open_release_stream("https://dosya.co/a/b.html", opener=RedirectOpener())


class BadContentOpener:
    def open(self, request, timeout=None):
        return Reply(b"<html>no</html>", 200, {"Content-Type": "text/html"})


def test_prevent_html_as_exe():
    with pytest.raises(DownloadError):
        open_release_stream(RELEASE, opener=BadContentOpener())
