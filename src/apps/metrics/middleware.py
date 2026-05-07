import contextlib

from apps.content.views import PostViewSet
from apps.metrics.events.signals import post_view_signal
from apps.metrics.events.types import PostViewEvent

BOT_KEYWORDS = ["bot", "crawl", "spider"]


def is_bot(user_agent: str) -> bool:
    return not user_agent or any(k in user_agent.lower() for k in BOT_KEYWORDS)


def anonymize_ip(ip: str | None) -> str | None:
    if not ip:
        return None

    if ":" in ip:
        parts = ip.split(":")
        return ":".join(parts[:4]) + "::"
    else:
        parts = ip.split(".")
        if len(parts) == 4:
            return ".".join(parts[:3]) + ".0"


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class PostViewTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code != 200:
            return response

        resolver = getattr(request, "resolver_match", None)
        if not resolver:
            return response

        view_func = resolver.func
        view_class = getattr(view_func, "cls", None)
        actions = getattr(view_func, "actions", {})

        if not view_class or not issubclass(view_class, PostViewSet):
            return response

        current_action = actions.get(request.method.lower())
        if current_action != "retrieve":
            return response

        ua = request.META.get("HTTP_USER_AGENT", "")
        if is_bot(ua):
            return response

        slug = resolver.kwargs.get("slug")
        if not slug:
            return response

        event = PostViewEvent(
            post_slug=slug,
            ip=anonymize_ip(get_client_ip(request)),
            user_agent=ua,
            referer=request.META.get("HTTP_REFERER"),
            user_id=str(request.user.id) if request.user.is_authenticated else None,
            is_bot=False,
        )

        with contextlib.suppress(Exception):
            post_view_signal.send(sender="post_view", event=event)

        return response
