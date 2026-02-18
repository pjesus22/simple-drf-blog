from django.core.management import call_command


def cleanup_deleted_uploads_task():
    """
    Scheduled task: deletes physical files for uploads soft-deleted more than 30
    days ago
    """
    call_command("cleanup_deleted_uploads")
