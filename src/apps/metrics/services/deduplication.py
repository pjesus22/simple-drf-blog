import hashlib
import json

from django.conf import settings
from django.core.cache import cache

DEFAULT_TTL = 300


def _extract_field_value(event: dict, field_spec: str | list[str]) -> str:
    """Extract field value(s) from event dict based on field specification."""
    if isinstance(field_spec, str):
        value = event.get(field_spec)
        return str(value) if value is not None else ""

    for field_name in field_spec:
        value = event.get(field_name)
        if value is not None:
            return str(value)

    return ""


def _get_dedup_config(event_type: str) -> tuple:
    """Get deduplication configuration for event type."""
    dedup_config = getattr(settings, "DEDUP_EVENT_CONFIG", {})
    event_config = dedup_config.get(event_type, {})

    if event_config:
        return event_config.get("fields", []), event_config.get("ttl", DEFAULT_TTL)

    return None, DEFAULT_TTL


def _build_canonical_key(event: dict, event_type: str) -> str:
    """Build canonical (sorted, deterministic) string for unknown event types."""
    sorted_event = {k: event[k] for k in sorted(event.keys())}
    canonical = json.dumps(sorted_event, sort_keys=True, default=str)
    return f"{event_type}:{canonical}"


def generate_key(event: dict, event_type: str) -> str:
    """Generate cache key for event."""
    fields_config, _ = _get_dedup_config(event_type)
    if fields_config is not None:
        field_values = []
        for field_spec in fields_config:
            value = _extract_field_value(event, field_spec)
            field_values.append(value)
        raw = ":".join(field_values)
        return f"metrics:{event_type}:{hashlib.sha256(raw.encode()).hexdigest()}"

    raw = _build_canonical_key(event, event_type)
    return f"metrics:{event_type}:{hashlib.sha256(raw.encode()).hexdigest()}"


def is_duplicate(event: dict, event_type: str = "post_view") -> bool:
    """Check if event is duplicate and set cache if not."""
    key = generate_key(event, event_type)
    _, ttl = _get_dedup_config(event_type)
    return not cache.add(key, 1, timeout=ttl)
