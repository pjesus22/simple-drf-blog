import os

from django.utils import timezone


def get_upload_path(instance, filename: str):
    name, ext = os.path.splitext(os.path.basename(filename))
    timestamp = timezone.now().strftime("%Y%m%d")
    return os.path.join(instance.purpose, timestamp, f"{instance.hash_sha256[:8]}{ext}")
