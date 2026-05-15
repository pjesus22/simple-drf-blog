from celery import shared_task

from apps.metrics.services import ingest_event


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_metric_event(event_type: str, event_data: dict) -> None:
    ingest_event(event_type, event_data)
