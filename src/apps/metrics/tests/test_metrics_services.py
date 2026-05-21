import pytest

from apps.metrics.models import MetricRecord
from apps.metrics.services.deduplication import (
    _build_canonical_key,
    _extract_field_value,
    _get_dedup_config,
    generate_key,
    is_duplicate,
)
from apps.metrics.services.ingestion import ingest_event


class TestDeduplicationServices:
    @pytest.mark.parametrize(
        "field_spec,expected_value",
        [
            ("post_slug", "test-post"),
            (["referer_domain", "ip_prefix"], "127.0.0.0"),
            ([], ""),
        ],
        ids=["single_value", "multiple_values_return_first_no_none", "empty_list"],
    )
    def test_extract_field_value(
        self, field_spec, expected_value, mock_post_view_event
    ):
        field_value = _extract_field_value(
            event=mock_post_view_event.get_metadata(),
            field_spec=field_spec,
        )
        assert field_value == expected_value

    @pytest.mark.parametrize(
        "event_type, expected_fields, expected_ttl",
        [
            ("mock_event", ["id1", "id2"], 10),
            ("unknown_event", None, 300),
        ],
        ids=["configured_event", "unconfigured_event"],
    )
    def test_get_dedup_config(
        self, event_type, expected_fields, expected_ttl, settings
    ):
        settings.DEDUP_EVENT_CONFIG = {
            "mock_event": {"fields": ["id1", "id2"], "ttl": 10},
        }
        fields, ttl = _get_dedup_config(event_type)

        assert fields == expected_fields
        assert ttl == expected_ttl

    def test_build_canonical_key_is_deterministic(self, mock_post_view_event):
        event_dict = mock_post_view_event.get_metadata()
        event_type = mock_post_view_event.event_type

        result1 = _build_canonical_key(event=event_dict, event_type=event_type)
        result2 = _build_canonical_key(event=event_dict, event_type=event_type)

        assert result1 == result2
        assert result1.startswith("post_view:")

    @pytest.mark.parametrize(
        "event_fixture, expected_prefix",
        [
            ("mock_post_view_event", "metrics:post_view:"),
            ("mock_unknown_event", "metrics:unknown_event:"),
        ],
        ids=["known_event", "unknown_event"],
    )
    def test_generate_key(
        self,
        event_fixture,
        expected_prefix,
        settings,
        mock_post_view_event,
        mock_unknown_event,
        request,
    ):
        settings.DEDUP_EVENT_CONFIG = {
            "post_view": {
                "fields": ["post_slug", "ip"],
                "ttl": 600,
            },
        }
        event = request.getfixturevalue(event_fixture)

        key = generate_key(
            event=event.get_metadata(),
            event_type=event.event_type,
        )

        assert key.startswith(expected_prefix)
        assert len(key) == len(expected_prefix) + 64

    def test_is_duplicate_returns_true_when_cached(
        self, mock_post_view_event, clear_cache
    ):
        uncached_event = mock_post_view_event

        is_dupe = is_duplicate(
            event=uncached_event.get_metadata(),
            event_type=uncached_event.event_type,
        )

        assert is_dupe is False

        cached_event = uncached_event

        is_dupe_cached = is_duplicate(
            event=cached_event.get_metadata(),
            event_type=cached_event.event_type,
        )
        assert is_dupe_cached is True


class TestIngestionServices:
    def test_ingest_event_return_none_when_duplicate(
        self, mocker, mock_post_view_event
    ):
        mocker.patch("apps.metrics.services.ingestion.is_duplicate", return_value=True)
        event = mock_post_view_event
        result = ingest_event(
            event_type=event.event_type,
            event_data=event.get_metadata(),
        )
        assert result is None

    def test_ingest_event_creates_record_when_not_duplicate(
        self, db, mocker, mock_post_view_event
    ):
        mocker.patch("apps.metrics.services.ingestion.is_duplicate", return_value=False)
        event = mock_post_view_event
        ingest_event(
            event_type=event.event_type,
            event_data=event.get_metadata(),
        )

        record = MetricRecord.objects.get(event_type=event.event_type)

        assert record.event_type == event.event_type
        assert record.metadata == event.get_metadata()
