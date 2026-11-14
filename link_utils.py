"""İndirme adreslerini sadece güvenilir HTTPS paylaşım/release adresleriyle sınırla."""
from urllib.parse import urlsplit


def validate_download_link(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Bağlantı metin olmalı")
    link = value.strip()
    if not link or len(link) > 2048 or any(ord(ch) < 32 or ord(ch) == 127 for ch in link):
        raise ValueError("Geçerli bir HTTPS indirme bağlantısı gir")
    try:
        parsed = urlsplit(link)
        port = parsed.port
        host = parsed.hostname
    except ValueError as exc:
        raise ValueError("Geçersiz bağlantı") from exc
    if (parsed.scheme.lower() != "https" or parsed.username or parsed.password
            or port not in (None, 443)):
        raise ValueError("Yalnızca güvenli HTTPS bağlantıları kullanılabilir")
    if host in ("dosya.co", "www.dosya.co"):
        if not parsed.path or parsed.path == "/":
            raise ValueError("Geçersiz dosya.co indirme bağlantısı")
    elif host == "github.com":
        # GitHub sürüm dosyalarına doğrudan giden bağlantılar; kod depoları değil.
        parts = parsed.path.strip("/").split("/")
        if (len(parts) < 6 or not parts[0] or not parts[1]
                or parts[2:4] != ["releases", "download"]
                or not parts[4] or not all(parts[5:])):
            raise ValueError("GitHub bağlantısı /kullanici/depo/releases/download/etiket/dosya biçiminde olmalı")
    else:
        raise ValueError("Yalnızca GitHub Releases veya dosya.co indirme bağlantıları kullanılabilir")
    return link


def download_host_name(valid_link: str) -> str:
    """Doğrulanmış indirme bağlantısının kullanıcıya gösterilen sağlayıcısı."""
    host = urlsplit(valid_link).hostname
    return "GitHub" if host == "github.com" else "dosya.co"
