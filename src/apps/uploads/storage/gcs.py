from storages.backends.gcloud import GoogleCloudStorage

from apps.uploads.storage.base import BaseMediaStorage


class GCSMediaStorage(GoogleCloudStorage, BaseMediaStorage):
    def get_backend_name(self) -> str:
        return "gcs"

    def health_check(self) -> bool:
        try:
            return self.client.bucket(self.bucket_name).exists()
        except Exception:
            return False
