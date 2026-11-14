"""Sadece dosya.co HTTPS adreslerini indirme bağlantısı olarak kabul et."""
from urllib.parse import urlsplit


def validate_download_link(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("dosya.co bağlantısı metin olmalı")
    link = value.strip()
    if not link or len(link) > 2048 or any(ord(ch) < 32 or ord(ch) == 127 for ch in link):
        raise ValueError("Geçerli bir dosya.co bağlantısı gir")
    try:
        parsed = urlsplit(link)
        port = parsed.port
        host = parsed.hostname
    except ValueError as exc:
        raise ValueError("Geçersiz bağlantı") from exc
    if (parsed.scheme.lower() != "https" or host not in ("dosya.co", "www.dosya.co")
            or parsed.username or parsed.password or port not in (None, 443)
            or not parsed.path or parsed.path == "/"):
        raise ValueError("Bağlantı https://dosya.co/... biçiminde olmalı")
    return link
