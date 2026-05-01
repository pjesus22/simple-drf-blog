from celery import shared_task
from django.core.management import call_command


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def cleanup_deleted_uploads_task(self, days=30, dry_run=False):
    call_command("cleanup_deleted_uploads", days=days, dry_run=dry_run)
