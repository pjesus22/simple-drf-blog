import hashlib
from unittest.mock import Mock

from apps.uploads.models import Upload
from apps.uploads.utils.path import get_upload_path
from django.utils import timezone


def test_get_upload_path_returns_correct_path():
    expected_hash = hashlib.sha256(b"test.jpg").hexdigest()
    expected_timestamp = timezone.now().strftime("%Y%m%d")
    upload = Mock(purpose=Upload.Purpose.ATTACHMENT, hash_sha256=expected_hash)

    path = get_upload_path(upload, "test.jpg")
    expected_path = (
        f"{upload.purpose.value}/{expected_timestamp}/{expected_hash[:8]}.jpg"
    )

    assert path == expected_path
