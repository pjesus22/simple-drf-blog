from dataclasses import dataclass

from .base import MetricEvent


@dataclass
class PostViewEvent(MetricEvent):
    post_slug: str
    ip: str | None
    user_agent: str
    referer: str | None
    user_id: str | None

    @property
    def event_type(self) -> str:
        return "post_view"
