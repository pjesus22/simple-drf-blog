from urllib.parse import urlparse

from crawlerdetect import CrawlerDetect

cd = CrawlerDetect()


def is_bot(user_agent: str) -> bool:
    return cd.isCrawler(user_agent)


def anonymize_ip(ip: str | None) -> str | None:
    if not ip:
        return None

    try:
        if ":" in ip:
            parts = ip.split(":")
            return ":".join(parts[:4]) + "::"
        else:
            parts = ip.split(".")
            if len(parts) == 4:
                return ".".join(parts[:3]) + ".0"
    except Exception:
        pass

    return None


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def parse_user_agent(user_agent: str) -> dict:
    ua = (user_agent or "").lower()

    browser = "Other"
    if "firefox" in ua:
        browser = "Firefox"
    elif "edg" in ua:
        browser = "Edge"
    elif "safari" in ua:
        browser = "Safari"
    elif "chrome" in ua:
        browser = "Chrome"

    os = "Other"
    if "windows" in ua:
        os = "Windows"
    elif "mac os" in ua or "macintosh" in ua:
        os = "macOS"
    elif "android" in ua:
        os = "Android"
    elif "iphone" in ua or "ipad" in ua or "ios" in ua:
        os = "iOS"
    elif "linux" in ua:
        os = "Linux"

    device = "Desktop"
    if "mobile" in ua:
        device = "Mobile"
    elif "tablet" in ua or "ipad" in ua:
        device = "Tablet"

    return {
        "browser": browser,
        "os": os,
        "device": device,
    }


def extract_referer_domain(referer: str | None) -> str | None:
    if not referer:
        return None

    try:
        parsed = urlparse(referer)
        return parsed.hostname
    except Exception:
        return None
