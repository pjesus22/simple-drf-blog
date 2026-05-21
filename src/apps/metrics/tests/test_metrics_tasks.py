from apps.metrics.tasks import process_metric_event


def test_process_metric_event_task(mocker, mock_post_view_event):
    mock_ingest_event = mocker.patch("apps.metrics.tasks.ingest_event")

    process_metric_event(
        mock_post_view_event.event_type, mock_post_view_event.get_metadata()
    )

    mock_ingest_event.assert_called_once_with(
        mock_post_view_event.event_type,
        mock_post_view_event.get_metadata(),
    )
