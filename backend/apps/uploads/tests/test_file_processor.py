import hashlib

import pytest
from apps.uploads.tests.helpers import make_file, make_image
from apps.uploads.utils import (
    AudioStrategy,
    BaseStrategy,
    DefaultStrategy,
    DocumentStrategy,
    FileProcessor,
    ImageStrategy,
    VideoStrategy,
)
from django.core.exceptions import ValidationError


class BrokenFile:
    name = "broken.bin"

    def seek(self, *args, **kwargs):
        raise OSError("seek failed")


def test_base_strategy_process_has_no_implementation():
    class MinimalStrategy(BaseStrategy):
        def process(self, file, head=None):
            return super().process(file, head)

    strategy = MinimalStrategy()
    test_file = make_file(content=b"test content")

    result = strategy.process(test_file)
    assert result is None


@pytest.mark.parametrize(
    "strategy, expected",
    [
        (VideoStrategy(), "video"),
        (AudioStrategy(), "audio"),
        (DocumentStrategy(), "document"),
        (DefaultStrategy(), "other"),
    ],
)
def test_process_non_image_strategies(strategy, expected):
    test_file = make_file(content=b"test content")
    result = strategy.process(test_file)

    assert result["file_type"] == expected


def test_process_image_strategy():
    test_file = make_image()
    strategy = ImageStrategy()
    result = strategy.process(test_file)

    assert result["file_type"] == "image"
    assert result["width"] == 50
    assert result["height"] == 30


def test_process_image_strategy_invalid_image():
    invalid_image_file = make_file(content=b"not an image")
    strategy = ImageStrategy()

    with pytest.raises(
        ValidationError, match="Uploaded file is not a valid or supported image."
    ):
        strategy.process(invalid_image_file)


def test_read_head_reads_and_resets_pointer():
    f = make_file(content=b"dummy_data")
    processor = FileProcessor(f)
    head = processor._read_head(5)

    assert head == b"dummy"
    assert f.tell() == 0


def test_detect_mime_type_without_magic():
    """
    Guesses the MIME type only from the file extension. If a file has no
    extension, it defaults to 'application/octet-stream'.
    """
    f = make_file(content=b"dummy", name="test.txt")
    processor = FileProcessor(f, use_magic=False)
    processor.detect_mime_type()

    assert processor.mime_type == "text/plain"


def test_detect_mime_type_with_magic():
    """
    Uses the `magic` library to detect the MIME type from file content.
    """
    f = make_file(content=b"%PDF-1.4 dummy pdf content", name="file.unknown")
    processor = FileProcessor(f, use_magic=True)
    processor.detect_mime_type()

    assert processor.mime_type == "application/pdf"


def test_detect_mime_type_exception_handling(monkeypatch):
    def fake_from_buffer(_data, mime=True):
        raise Exception("Simulated failure")

    monkeypatch.setattr(
        "apps.uploads.utils.file_processor.magic.from_buffer", fake_from_buffer
    )

    f = make_file(content=b"some data")
    processor = FileProcessor(f, use_magic=True)
    processor.detect_mime_type()

    assert processor.mime_type == "application/octet-stream"


def test_select_strategy_image():
    f = make_image(format="PNG")
    processor = FileProcessor(f, use_magic=False)

    processor.detect_mime_type()
    strategy = processor.select_strategy()

    assert isinstance(strategy, ImageStrategy)


def test_select_strategy_default():
    f = make_file(content=b"unknown content")
    processor = FileProcessor(f)

    strategy = processor.select_strategy()

    assert isinstance(strategy, DefaultStrategy)


def test_compute_md5_correct_hash():
    test_content = b"hello world"
    f = make_file(content=test_content)
    processor = FileProcessor(f)

    expected = hashlib.md5(test_content).hexdigest()

    assert processor.compute_md5() == expected


def test_get_size_from_attribute():
    test_content = b"hello world"
    f = make_file(content=test_content)
    processor = FileProcessor(f)

    f.size = len(test_content)

    assert processor._get_size() == len(test_content)


def test_get_size_from_file():
    test_content = b"hello world"
    f = make_file(content=test_content)
    processor = FileProcessor(f)

    assert processor._get_size() == len(test_content)


def test_get_size_from_file_no_size():
    f = make_file(content=b"")
    processor = FileProcessor(f)

    with pytest.raises(ValidationError, match="Empty or broken file."):
        processor._get_size()


def test_get_size_raises_exception_for_broken_file():
    broken_file = BrokenFile()
    processor = FileProcessor(broken_file)

    with pytest.raises(ValidationError, match="Could not determine file size: .*"):
        processor._get_size()


def test_process_valid_file():
    f = make_file(content=b"%PDF-1.4 dummy pdf content", name="file.pdf")
    processor = FileProcessor(f)

    meta = processor.process()
    assert meta["file_type"] == "document"
    assert meta["original_filename"] == "file.pdf"
    assert meta["mime_type"] == "application/pdf"
    assert "hash_md5" in meta
    assert "size" in meta


def test_process_raises_exception_when_no_file():
    with pytest.raises(ValidationError, match="No file provided."):
        FileProcessor(None).process()


@pytest.mark.parametrize(
    "size",
    [10 * 1024**2 + 1, 10 * 1024**2, 10 * 1024**2 - 1],
    ids=["too_large", "max_size", "below_max_size"],
)
def test_process_raises_exception_size_limits(size):
    max_size = 10 * 1024**2
    f = make_file(content=b"0" * size)
    processor = FileProcessor(f)

    if size > max_size:
        with pytest.raises(
            expected_exception=ValidationError,
            match="The file exceeds the maximum size permitted.",
        ):
            processor.process()
    else:
        processor.process()
        assert True
