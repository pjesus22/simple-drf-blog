from dataclasses import dataclass


@dataclass
class PostViewEvent:
    post_slug: str
    ip: str | None
    user_agent: str
    referer: str | None
    user_id: str | None
    is_bot: bool
