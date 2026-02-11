from datetime import datetime
import hashlib

import pytest

from apps.uploads.models import Upload
from apps.uploads.utils.path import get_upload_path


@pytest.mark.parametrize(
    "purpose, filename, expected_hash, expected_ext",
    [
        (Upload.Purpose.ATTACHMENT, "test.jpg", "test.jpg", ".jpg"),
        (Upload.Purpose.AVATAR, "profile.png", "profile.png", ".png"),
        (Upload.Purpose.ATTACHMENT, "no_ext", "no_ext", ""),
    ],
    ids=("attachment", "avatar", "no_extension"),
)
def test_get_upload_path_returns_correct_path(
    mocker, purpose, filename, expected_hash, expected_ext
):
    fixed_now = datetime(2024, 1, 1, 12, 0, 0)
    mocker.patch("django.utils.timezone.now", return_value=fixed_now)

    hash_val = hashlib.sha256(expected_hash.encode()).hexdigest()
    upload = mocker.Mock(purpose=purpose, hash_sha256=hash_val)

    path = get_upload_path(upload, filename)

    expected_timestamp = fixed_now.strftime("%Y%m%d")
    expected_path = f"{purpose.value}/{expected_timestamp}/{hash_val[:8]}{expected_ext}"

    assert path == expected_path
