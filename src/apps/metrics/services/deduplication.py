import hashlib

from django.conf import settings
from django.core.cache import cache


def generate_key(event: dict) -> str:
    raw = (
        f"{event.get('post_slug')}"
        f":{event.get('user_id') or event.get('ip')}"
        f":{event.get('user_agent')}"
    )
    return f"metrics:{hashlib.sha256(raw.encode('utf-8')).hexdigest()}"


def is_duplicate(event: dict) -> bool:
    key = generate_key(event)
    if cache.get(key):
        return True
    cache.set(key, 1, timeout=getattr(settings, "POST_VIEW_DEDUP_TTL", 300))
    return False
