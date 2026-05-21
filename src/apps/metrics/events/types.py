from dataclasses import InitVar, dataclass, field

from apps.metrics.utils import (
    anonymize_ip,
    extract_referer_domain,
    get_best_client_ip,
    parse_user_agent,
)

from .base import MetricEvent


@dataclass
class PostViewEvent(MetricEvent):
    post_slug: str
    ip_prefix: str | None = field(init=False)
    browser: str = field(init=False)
    os: str = field(init=False)
    device: str = field(init=False)
    referer_domain: str | None
    authenticated: bool

    user_agent: InitVar[str] = ""
    client_ip: InitVar[str | None] = None

    @property
    def event_type(self) -> str:
        return "post_view"

    def __post_init__(self, user_agent: str, client_ip: str | None):
        self.ip_prefix = anonymize_ip(client_ip)
        ua_data = parse_user_agent(user_agent)
        self.browser = ua_data["browser"]
        self.os = ua_data["os"]
        self.device = ua_data["device"]

    @classmethod
    def from_request(cls, request, slug: str):
        return cls(
            post_slug=slug,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            client_ip=get_best_client_ip(request),
            referer_domain=extract_referer_domain(request.META.get("HTTP_REFERER")),
            authenticated=request.user.is_authenticated,
        )
