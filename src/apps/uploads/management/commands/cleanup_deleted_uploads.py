from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.uploads.models import Upload


class Command(BaseCommand):
    help = "Delete files for soft-deleted uploads older than 30 days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to keep soft-deleted uploads",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        cutoff = timezone.now() - timedelta(days=days)
        old_uploads = Upload.all_objects.filter(
            deleted_at__isnull=False, deleted_at__lt=cutoff
        )

        count = old_uploads.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would delete {count} uploads older than {days} days"
                )
            )
            for upload in old_uploads[:10]:
                self.stdout.write(
                    f"  - {upload.original_filename} "
                    f"(deleted: {upload.deleted_at.strftime('%Y-%m-%d')})"
                )
            if count > 10:
                self.stdout.write(f" ... and {count - 10} more")
            return

        deleted_count = 0
        failed_count = 0

        for upload in old_uploads:
            try:
                file_name = upload.file.name
                upload.file.delete(save=False)
                upload.delete()
                deleted_count += 1
                self.stdout.write(f"Deleted: {file_name}")
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Failed to delete {upload.id}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCleaned up {deleted_count} uploads ({failed_count} failed)"
            )
        )
