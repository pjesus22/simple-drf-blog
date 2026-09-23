from datetime import datetime
import hashlib

import pytest

from apps.uploads.models import Upload
from apps.uploads.utils.path import (
    build_upload_relpath,
    get_upload_path,
    is_private_storage_path,
)


@pytest.mark.parametrize(
    "purpose, filename, expected_hash, expected_ext, visibility",
    [
        pytest.param(
            Upload.Purpose.ATTACHMENT,
            "test.jpg",
            "test.jpg",
            ".jpg",
            Upload.Visibility.PUBLIC,
            id="attachment_public",
        ),
        pytest.param(
            Upload.Purpose.AVATAR,
            "profile.png",
            "profile.png",
            ".png",
            Upload.Visibility.PRIVATE,
            id="avatar_private",
        ),
        pytest.param(
            Upload.Purpose.ATTACHMENT,
            "no_ext",
            "no_ext",
            "",
            Upload.Visibility.PUBLIC,
            id="no_extension_public",
        ),
    ],
)
def test_get_upload_path_returns_correct_path(
    mocker, purpose, filename, expected_hash, expected_ext, visibility
):
    fixed_now = datetime(2024, 1, 1, 12, 0, 0)
    mocker.patch("django.utils.timezone.now", return_value=fixed_now)

    hash_val = hashlib.sha256(expected_hash.encode()).hexdigest()
    upload = mocker.Mock(
        purpose=purpose,
        hash_sha256=hash_val,
        visibility=visibility,
        Visibility=Upload.Visibility,
    )

    path = get_upload_path(upload, filename)

    expected_timestamp = fixed_now.strftime("%Y%m%d")
    expected_path = f"{purpose.value}/{expected_timestamp}/{hash_val[:8]}{expected_ext}"
    if visibility == Upload.Visibility.PRIVATE:
        expected_path = f"private/{expected_path}"

    assert path == expected_path


@pytest.mark.parametrize(
    "name, expected",
    [
        ("private/avatar/240101/abcd1234.png", True),
        ("avatar/240101/abcd1234.png", False),
        ("privatex/avatar/240101/abcd1234.png", False),
        ("private", False),
        ("foo/private/bar.txt", False),
    ],
    ids=("private_prefix", "public", "privatex", "no_slash", "mid_path"),
)
def test_is_private_storage_path(name, expected):
    assert is_private_storage_path(name) is expected


def test_build_upload_relpath_no_private_prefix(mocker):
    fixed_now = datetime(24, 1, 1, 0, 0, 0)
    mocker.patch("django.utils.timezone.now", return_value=fixed_now)

    hash_val = hashlib.sha256(b"x").hexdigest()
    instance = mocker.Mock(
        purpose=Upload.Purpose.AVATAR,
        hash_sha256=hash_val,
        visibility=Upload.Visibility.PRIVATE,
    )

    path = build_upload_relpath(instance, "pic.png")

    assert not path.startswith("/private")
    assert path == f"avatar/240101/{hash_val[:8]}.png"
