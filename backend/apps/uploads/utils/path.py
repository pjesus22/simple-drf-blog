import os

from django.utils import timezone


def get_upload_path(instance, filename: str):
    base_name = os.path.basename(filename)
    timestamp = timezone.now().strftime("%Y%m%d")
    purpose = instance.purpose
    return os.path.join(purpose, timestamp, base_name)
