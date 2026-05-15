from collections.abc import Callable


class EventRegistry:
    """Registry for event handlers."""

    _handlers: dict[str, Callable] = {}

    @classmethod
    def register_handler(cls, event_type: str, handler: Callable) -> None:
        cls._handlers[event_type] = handler

    @classmethod
    def get_handler(cls, event_type: str) -> Callable | None:
        return cls._handlers.get(event_type)

    @classmethod
    def is_registered(cls, event_type: str) -> bool:
        return event_type in cls._handlers
