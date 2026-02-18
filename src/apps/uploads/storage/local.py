import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from apps.uploads.storage.base import BaseMediaStorage


class LocalMediaStorage(FileSystemStorage, BaseMediaStorage):
    def __init__(self):
        super().__init__(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)

    def get_backend_name(self) -> str:
        return "local"

    def health_check(self) -> bool:
        return os.path.isdir(self.location) and os.access(self.location, os.W_OK)
