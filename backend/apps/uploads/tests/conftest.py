from unittest.mock import patch

import pytest
from pytest_factoryboy import register
from tests.factories import EditorFactory, UploadFactory

register(EditorFactory)
register(UploadFactory)


@pytest.fixture(autouse=True)
def clean_media(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    yield


@pytest.fixture
def mock_file_processor():
    patchers = []

    def _mock(meta=None):
        fake_meta = meta or {
            "mime_type": "text/plain",
            "hash_md5": "fakehashmd5",
            "size": 1234,
            "original_filename": "test.txt",
            "file_type": "document",
        }

        patcher = patch(
            "apps.uploads.utils.file_processor.FileProcessor.process",
            return_value=fake_meta,
        )
        mock = patcher.start()
        patchers.append(patcher)
        return mock

    yield _mock

    for patcher in patchers:
        patcher.stop()
