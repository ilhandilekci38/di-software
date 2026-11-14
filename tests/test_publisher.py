"""Bağlantı doğrulaması; yayınlama için sunucuya EXE yüklenmez."""
import pytest
from link_utils import download_host_name, validate_download_link


@pytest.mark.parametrize("url,host", [
    ("https://dosya.co/a/demo.html", "dosya.co"),
    ("https://www.dosya.co/a/demo.html", "dosya.co"),
    ("https://github.com/ilhandilekci38/di-software/releases/download/27/di-ato.27.exe", "GitHub"),
    ("https://github.com/ilhandilekci38/di-software/releases/download/27/di-browser.exe", "GitHub"),
    ("https://github.com/ilhandilekci38/di-software/releases/download/27/pydi-ide.exe", "GitHub"),
])
def test_allowed_release_url(url, host):
    assert validate_download_link(url) == url
    assert download_host_name(url) == host


@pytest.mark.parametrize("url", [
    "", "javascript:alert(1)", "http://dosya.co/abc", "https://notdosya.co/demo",
    "https://dosya.co.evil.com/demo", "https://user@dosya.co/demo",
    "https://dosya.co/", "https://dosya.co:444/demo", "https://dosya.co/abc\nfoo",
    "https://github.com/ilhandilekci38/di-software", "https://github.com/ilhandilekci38/di-software/releases",
    "https://github.com.evil.com/ilhandilekci38/di-software/releases/download/27/x.exe",
    "https://github.com/ilhandilekci38/di-software/releases/download/27/",
    "https://github.com:444/ilhandilekci38/di-software/releases/download/27/x.exe",
    "file:///C:/secret", "https://example.com/malware.exe",
])
def test_reject_untrusted_url(url):
    with pytest.raises(ValueError):
        validate_download_link(url)
