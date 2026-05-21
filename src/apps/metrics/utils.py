import logging
from urllib.parse import urlparse

from django.conf import settings
from ipware import get_client_ip
from user_agents import parse

logger = logging.getLogger(__name__)


def is_bot(user_agent: str) -> bool:
    if not user_agent:
        return True
    return parse(user_agent).is_bot


def anonymize_ip(ip: str | None = None) -> str | None:
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


def get_best_client_ip(request):
    client_ip, is_routable = get_client_ip(request)

    if not client_ip:
        return "0.0.0.0"

    if not is_routable and not settings.DEBUG:
        logger.warning(
            f"SECURITY: Unroutable/Private IP detected -> {client_ip}. "
            "Check NGINX proxy configuration or potential spoofing attempt."
        )
    return client_ip


def parse_user_agent(user_agent: str) -> dict:
    ua = parse(user_agent)

    return {
        "browser": ua.browser.family,
        "os": ua.os.family,
        "device": ua.device.family,
    }


def extract_referer_domain(referer: str | None) -> str | None:
    if not referer:
        return None

    try:
        parsed = urlparse(referer)
        return parsed.hostname
    except Exception:
        return None
