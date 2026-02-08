import hashlib

import pytest
from apps.uploads.exceptions import (
    FileTooLargeError,
    InvalidFileError,
    UnsupportedMimeTypeError,
)
from apps.uploads.tests.helpers import FileFactory as ff
from apps.uploads.utils import DefaultStrategy, FileProcessor, ImageStrategy
from apps.uploads.utils.file_processor import BaseStrategy, validate_extension
from django.core.files.uploadedfile import SimpleUploadedFile
from faker import Faker

fake = Faker()


class TestValidateExtension:
    def test_validate_extension_success(self):
        validate_extension(
            "image/jpeg",
            filename=fake.file_path(
                extension="jpg",
                file_system_rule="linux",
                depth=2,
            ),
        )

    def test_validate_extension_raises_invalid_file_error_file_without_extension(self):
        with pytest.raises(
            InvalidFileError,
            match="Uploaded file has no extension.",
        ):
            validate_extension(
                "image/jpeg",
                filename=fake.file_path(
                    extension="",
                    file_system_rule="linux",
                    depth=2,
                ),
            )

    def test_validate_extension_raises_unsupported_mime_type_error(self):
        with pytest.raises(UnsupportedMimeTypeError, match="not allowed"):
            validate_extension(
                "application/x-dosexec",
                filename=fake.file_path(
                    extension="exe",
                    file_system_rule="linux",
                    depth=2,
                ),
            )

    def test_validate_extension_raises_invalid_file_error_extension_not_match_mime_type(
        self,
    ):
        with pytest.raises(
            InvalidFileError,
            match="File extension '.jpg' is not allowed for MIME type 'text/plain'.",
        ):
            validate_extension(
                "text/plain",
                filename=fake.file_path(
                    extension="jpg",
                    file_system_rule="linux",
                    depth=2,
                ),
            )


class TestStrategies:
    def test_base_strategy_process_is_abstract(self):
        class MockStrategy(BaseStrategy):
            def process(self, file, head):
                return super().process(file, head)

        strategy = MockStrategy()
        f = SimpleUploadedFile("test.txt", b"test content")

        with pytest.raises(NotImplementedError):
            strategy.process(f, b"test")

    def test_image_strategy_valid_image(self):
        f = ff.create_real_image_file(size=(50, 30))
        strategy = ImageStrategy()

        result = strategy.process(f, f.read(2048))

        assert result["width"] == 50
        assert result["height"] == 30

    def test_image_strategy_invalid_image(self):
        f = SimpleUploadedFile("test.png", b"test content")
        strategy = ImageStrategy()

        with pytest.raises(
            InvalidFileError, match="Uploaded file is not a valid or supported image."
        ):
            strategy.process(f, b"not image")

    def test_default_strategy_returns_empty_dict(self):
        f = SimpleUploadedFile("test.txt", b"test content")
        strategy = DefaultStrategy()

        result = strategy.process(f, b"test")

        assert result == {}


class TestFileProcessor:
    def test_file_processor_stream_file_success(self):
        f = ff.create_real_text_file()
        processor = FileProcessor(file_obj=f)

        size, head, sha256 = processor._stream_file()

        f.seek(0)
        assert size == f.size
        assert head == f.read(2048)

        f.seek(0)
        assert sha256 == hashlib.sha256(f.read()).hexdigest()

    def test_file_processor_stream_file_raises_file_too_large_error(self):
        f = ff.create_mock_file(content=b"0" * (10 * 1024**2 + 1))
        processor = FileProcessor(file_obj=f)

        with pytest.raises(FileTooLargeError, match="File size exceeds the limit."):
            processor._stream_file()

    def test_file_processor_stream_file_raises_invalid_file_error_for_empty_file(self):
        f = SimpleUploadedFile("test.txt", b"")
        processor = FileProcessor(file_obj=f)

        with pytest.raises(InvalidFileError, match="Empty or broken file."):
            processor._stream_file()

    def test_file_processor_detect_mime_with_magic(self):
        f = ff.create_real_pdf_file()
        processor = FileProcessor(file_obj=f, use_magic=True)
        head = f.read(2048)

        mime = processor._detect_mime(head)

        assert mime == "application/pdf"

    def test_file_processor_detect_mime_guesses_by_name(self):
        f = ff.create_mock_file()
        processor = FileProcessor(file_obj=f, use_magic=False)
        head = b"dummy head"

        mime = processor._detect_mime(head)

        assert mime == "text/plain"

    def test_file_processor_detect_mime_not_allowed_type(self):
        f = ff.create_mock_file(content=b"MZ...", name="app.exe")
        processor = FileProcessor(file_obj=f, use_magic=False)

        with pytest.raises(UnsupportedMimeTypeError, match="Unsupported MIME type."):
            processor._detect_mime(b"MZ head")

    def test_file_processor_detect_mime_exception_fallback(self, monkeypatch):
        def fake_from_buffer(_data, mime=True):
            raise Exception("Simulated failure")

        monkeypatch.setattr(
            "apps.uploads.utils.file_processor.magic.from_buffer", fake_from_buffer
        )
        f = ff.create_mock_file()
        processor = FileProcessor(file_obj=f, use_magic=True)
        mime = processor._detect_mime(b"some data")
        assert mime == "text/plain"

    def test_file_processor_select_strategy_routing(self):
        processor = FileProcessor(None)
        assert isinstance(processor._select_strategy("image/jpeg"), ImageStrategy)
        assert isinstance(
            processor._select_strategy("application/pdf"), DefaultStrategy
        )

    def test_file_processor_process_full_flow_success(self):
        f = ff.create_real_pdf_file()
        processor = FileProcessor(file_obj=f)
        result = processor.process()

        assert result["mime_type"] == "application/pdf"
        assert "hash_sha256" in result
        assert result["size"] == f.size
        assert result["original_filename"] == "test.pdf"

    def test_file_processor_process_no_file_raises_error(self):
        with pytest.raises(InvalidFileError, match="Invalid file provided."):
            FileProcessor(None).process()

    def test_file_processor_process_resets_file_pointer(self):
        f = ff.create_mock_file()
        f.seek(5)
        processor = FileProcessor(file_obj=f)
        processor.process()
        assert f.tell() == 0

    @pytest.mark.parametrize(
        "size_offset, expected_error",
        [
            (1, FileTooLargeError),
            (0, None),
            (-1, None),
        ],
        ids=["too_large", "max_size", "below_max_size"],
    )
    def test_file_processor_process_size_limits(self, size_offset, expected_error):
        max_size = 100
        size = max_size + size_offset
        f = ff.create_mock_file(content=b"0" * size)
        processor = FileProcessor(file_obj=f, max_size=max_size)

        if expected_error:
            with pytest.raises(expected_error, match="File size exceeds the limit."):
                processor.process()
        else:
            result = processor.process()
            assert result["size"] == size
