import pytest

from apps.content.views import PostViewSet
from apps.metrics.middleware import PostViewTrackingMiddleware


@pytest.fixture
def mock_request(mocker, rf):
    def _make(**overrides):
        req = rf.get("/posts/test/")
        req.method = overrides.get("method", "GET")
        req.META.update(overrides.get("META", {"HTTP_USER_AGENT": "Mozilla/5.0"}))
        req.user = mocker.MagicMock(is_authenticated=True)

        resolver = mocker.MagicMock()
        resolver.func.cls = overrides.get("view_class", PostViewSet)
        resolver.func.actions = overrides.get("action", {"get": "retrieve"})
        resolver.kwargs = overrides.get("kwargs", {"slug": "test"})
        req.resolver_match = overrides.get("resolver_match", resolver)
        return req

    return _make


class TestPostViewTrackingMiddleware:
    @pytest.mark.parametrize("status_code", [404, 500, 403, 301])
    def test_no_event_when_response_is_not_200(self, mocker, mock_request, status_code):
        mock_send = mocker.patch("apps.metrics.events.bus.EventBus.send")
        response = mocker.MagicMock(status_code=status_code)

        middleware = PostViewTrackingMiddleware(response)
        middleware(mock_request())

        mock_send.assert_not_called()

    def test_no_event_when_no_resolver_match(self, mocker, mock_request):
        mock_send = mocker.patch("apps.metrics.events.bus.EventBus.send")
        request = mock_request(resolver_match=None)
        response = mocker.MagicMock(status_code=200)
        get_response = mocker.MagicMock(return_value=response)

        middleware = PostViewTrackingMiddleware(get_response)
        middleware(request)

        mock_send.assert_not_called()

    def test_no_event_when_dnt_enabled(self, mocker, mock_request):
        mock_send = mocker.patch("apps.metrics.events.bus.EventBus.send")
        request = mock_request(META={"HTTP_DNT": "1"})
        response = mocker.MagicMock(status_code=200)
        get_response = mocker.MagicMock(return_value=response)

        middleware = PostViewTrackingMiddleware(get_response)
        middleware(request)

        mock_send.assert_not_called()

    def test_no_event_when_view_not_post_viewset(self, mocker, mock_request):
        mock_send = mocker.patch("apps.metrics.events.bus.EventBus.send")
        request = mock_request(view_class=object)
        response = mocker.MagicMock(status_code=200)
        get_response = mocker.MagicMock(return_value=response)

        middleware = PostViewTrackingMiddleware(get_response)
        middleware(request)

        mock_send.assert_not_called()

    def test_no_event_when_action_is_not_retrieve(self, mocker, mock_request):
        mock_send = mocker.patch("apps.metrics.events.bus.EventBus.send")
        request = mock_request(action={"get": "list"})
        response = mocker.MagicMock(status_code=200)
        get_response = mocker.MagicMock(return_value=response)

        middleware = PostViewTrackingMiddleware(get_response)
        middleware(request)

        mock_send.assert_not_called()

    def test_no_event_when_no_slug(self, mocker, mock_request):
        mock_send = mocker.patch("apps.metrics.events.bus.EventBus.send")
        request = mock_request(kwargs={})
        response = mocker.MagicMock(status_code=200)
        get_response = mocker.MagicMock(return_value=response)

        middleware = PostViewTrackingMiddleware(get_response)
        middleware(request)

        mock_send.assert_not_called()

    @pytest.mark.parametrize(
        "user_agent", ["Googlebot/2.1", "Bingbot/1.0", "spider-bot", ""]
    )
    def test_no_event_when_bot_user_agent(self, user_agent, mocker, mock_request):
        mock_send = mocker.patch("apps.metrics.events.bus.EventBus.send")
        request = mock_request(META={"HTTP_USER_AGENT": user_agent})
        response = mocker.MagicMock(status_code=200)
        get_response = mocker.MagicMock(return_value=response)

        middleware = PostViewTrackingMiddleware(get_response)
        middleware(request)

        mock_send.assert_not_called()

    def test_sends_event_on_valid_retrieve_request(self, mocker, mock_request):
        mock_send = mocker.patch("apps.metrics.events.bus.EventBus.send")
        mock_event = mocker.MagicMock()
        mocker.patch(
            "apps.metrics.events.types.PostViewEvent.from_request",
            return_value=mock_event,
        )
        response = mocker.MagicMock(status_code=200)
        get_response = mocker.MagicMock(return_value=response)

        middleware = PostViewTrackingMiddleware(get_response)
        middleware(mock_request())

        mock_send.assert_called_once_with(mock_event)

    @pytest.mark.parametrize("exc", [ConnectionError, TimeoutError])
    def test_response_returned_when_event_bus_raises_error(
        self, mocker, mock_request, exc
    ):
        mock_send = mocker.patch(
            "apps.metrics.events.bus.EventBus.send",
            side_effect=exc,
        )
        mock_event = mocker.MagicMock()
        mocker.patch(
            "apps.metrics.events.types.PostViewEvent.from_request",
            return_value=mock_event,
        )
        response = mocker.MagicMock(status_code=200)
        get_response = mocker.MagicMock(return_value=response)

        middleware = PostViewTrackingMiddleware(get_response)
        result = middleware(mock_request())

        assert result == response
        mock_send.assert_called_once_with(mock_event)
