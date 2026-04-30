from celery import shared_task

from apps.metrics.services import ingest_post_view


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def process_post_view_event(self, event_dict):
    ingest_post_view(event_dict)
