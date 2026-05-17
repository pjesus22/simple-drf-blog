import contextlib

from apps.content.views import PostViewSet
from apps.metrics.events.bus import EventBus
from apps.metrics.events.types import PostViewEvent
from apps.metrics.utils import is_bot


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

        if request.META.get("HTTP_DNT") == "1":
            return response

        view_func = resolver.func
        view_class = getattr(view_func, "cls", None)
        actions = getattr(view_func, "actions", {})
        if not view_class or not issubclass(view_class, PostViewSet):
            return response

        current_action = actions.get(request.method.lower())
        if current_action != "retrieve":
            return response

        slug = resolver.kwargs.get("slug")
        if not slug:
            return response

        if is_bot(request.META.get("HTTP_USER_AGENT", "")):
            return response

        event = PostViewEvent.from_request(request, slug)

        with contextlib.suppress(ConnectionError, TimeoutError):
            EventBus.send(event)

        return response
