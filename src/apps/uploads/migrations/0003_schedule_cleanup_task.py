from django.db import migrations


def create_schedule(apps, schema_editor):
    Schedule = apps.get_model("django_q", "Schedule")
    Schedule.objects.get_or_create(
        func="apps.uploads.tasks.cleanup_deleted_uploads_task",
        defaults={
            "name": "Cleanup deleted uploads",
            "schedule_type": "D",
            "repeats": -1,
        }
    )

def remove_schedule(apps, schema_editor):
    Schedule = apps.get_model("django_q", "Schedule")
    Schedule.objects.filter(
        func="apps.uploads.tasks.cleanup_deleted_uploads_task",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("uploads", "0002_add_soft_delete_support"),
        ("django_q", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_schedule, remove_schedule)
    ]
