from dataclasses import dataclass

from apps.metrics.events.base import MetricEvent
from apps.metrics.events.bus import EventBus
from apps.metrics.events.handlers import PostViewHandler, handle_metric_event
from apps.metrics.events.registry import EventRegistry
from apps.metrics.events.types import PostViewEvent


@dataclass
class MockMetricEvent(MetricEvent):
    field1: str
    field2: str

    @property
    def event_type(self):
        return "mock_event"


class TestBaseEvent:
    def test_metric_event_event_type(self):
        mme = MockMetricEvent(field1="test1", field2="test2")
        assert mme.event_type == "mock_event"

    def test_metric_event_get_metadata(self):
        mme = MockMetricEvent(field1="test1", field2="test2")
        assert mme.get_metadata() == {"field1": "test1", "field2": "test2"}

    def test_metric_event_validate(self):
        mme = MockMetricEvent(field1="test1", field2="test2")
        assert mme.validate()


class TestBus:
    def test_event_bus_sends_signal(self, mocker):
        mock_signal = mocker.patch("apps.metrics.events.bus.metric_event_signal")
        event = mocker.MagicMock(event_type="mock_event")
        EventBus.send(event)
        mock_signal.send.assert_called_once_with(event=event, sender=event.event_type)

    def test_event_bus_does_not_send_signal_if_invalid(
        self, mocker, mock_unknown_event
    ):
        mock_signal = mocker.patch("apps.metrics.events.signals.metric_event_signal")
        mocker.patch.object(mock_unknown_event, "validate", return_value=False)
        EventBus.send(mock_unknown_event)
        mock_signal.send.assert_not_called()


class TestHandlers:
    def test_handle_metric_event_dispatches_to_appropriate_handler(self, mocker):
        event = mocker.MagicMock(event_type="test_event")
        handler = mocker.MagicMock()
        mocker.patch.object(EventRegistry, "get_handler", return_value=handler)

        handle_metric_event(sender="test_event", event=event)

        handler.assert_called_once_with(event)

    def test_does_nothing_when_no_handler_registered(self, mocker):
        event = mocker.MagicMock(event_type="unknown_event")
        mocker.patch.object(EventRegistry, "get_handler", return_value=None)

        handle_metric_event(sender="unknown_event", event=event)

    def test_post_view_handler_calls_process_metric_event(
        self, mocker, mock_post_view_event
    ):
        event = mock_post_view_event
        handler = PostViewHandler()
        mock_task = mocker.patch("apps.metrics.events.handlers.process_metric_event")

        handler(event)

        mock_task.delay.assert_called_once_with(
            event_type=event.event_type,
            event_data=event.get_metadata(),
        )


class TestRegistry:
    def test_event_registry_register_handler(self):
        registry = EventRegistry()
        registry.register_handler("test", lambda e: None)
        assert registry.is_registered("test")

    def test_event_registry_get_handler(self):
        registry = EventRegistry()
        registry.register_handler("test", lambda e: None)
        handler = registry.get_handler("test")
        assert callable(handler)

    def test_event_registry_is_registered(self):
        registry = EventRegistry()
        registry.register_handler("test", lambda e: None)
        assert registry.is_registered("test")

    def test_event_registry_get_handler_returns_none_for_unregistered(self):
        registry = EventRegistry()
        assert registry.get_handler("nonexistent") is None

    def test_event_registry_is_registered_returns_false_for_unregistered(self):
        registry = EventRegistry()
        assert registry.is_registered("nonexistent") is False

    def test_event_registry_overwrites_handler(self, mocker):
        registry = EventRegistry()
        replacement = mocker.MagicMock()

        registry.register_handler("test", lambda e: "original")
        registry.register_handler("test", replacement)

        assert registry.get_handler("test") is replacement


class TestEventTypes:
    def test_from_request_creates_event(self, mocker):
        request = mocker.MagicMock(
            META={"HTTP_USER_AGENT": "foo", "HTTP_REFERER": "https://example.com/page"},
            user=mocker.MagicMock(is_authenticated=True),
        )
        mocker.patch("apps.metrics.events.types.anonymize_ip", return_value="192.168.1")
        mocker.patch(
            "apps.metrics.events.types.parse_user_agent",
            return_value={"browser": "Chrome", "os": "Linux", "device": "desktop"},
        )
        mocker.patch(
            "apps.metrics.events.types.get_best_client_ip", return_value="192.168.1.5"
        )
        mocker.patch(
            "apps.metrics.events.types.extract_referer_domain",
            return_value="example.com",
        )
        event = PostViewEvent.from_request(request, slug="test-post")
        assert event.post_slug == "test-post"
        assert event.ip_prefix == "192.168.1"
        assert event.browser == "Chrome"
        assert event.os == "Linux"
        assert event.device == "desktop"
        assert event.referer_domain == "example.com"
        assert event.authenticated is True
