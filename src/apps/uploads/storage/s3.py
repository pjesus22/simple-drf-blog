from storages.backends.s3boto3 import S3Boto3Storage

from apps.uploads.storage.base import BaseMediaStorage


class S3MediaStorage(S3Boto3Storage, BaseMediaStorage):
    def get_backend_name(self) -> str:
        return "s3"

    def health_check(self) -> bool:
        try:
            self.connection.meta.client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception:
            return False
