import hashlib

import pytest
from apps.uploads.exceptions import (
    FileTooLargeError,
    InvalidFileError,
    UnsupportedMimeTypeError,
)
from apps.uploads.utils import DefaultStrategy, FileProcessor, ImageStrategy
from apps.uploads.utils.file_processor import BaseStrategy, validate_extension
from django.core.files.uploadedfile import SimpleUploadedFile


class TestValidateExtension:
    @pytest.mark.parametrize(
        "mime_type, extension, expected_error, match",
        [
            ("image/jpeg", "jpg", None, None),
            (
                "image/jpeg",
                "",
                InvalidFileError,
                "Uploaded file has no extension.",
            ),
            (
                "application/x-dosexec",
                "exe",
                UnsupportedMimeTypeError,
                "not allowed",
            ),
            (
                "text/plain",
                "jpg",
                InvalidFileError,
                "File extension '.jpg' is not allowed for MIME type 'text/plain'.",
            ),
        ],
        ids=("success", "no_extension", "unsupported_mime", "mismatch"),
    )
    def test_validate_extension(
        self, faker, mime_type, extension, expected_error, match
    ):
        filename = faker.file_path(
            extension=extension,
            file_system_rule="linux",
            depth=2,
        )

        if expected_error:
            with pytest.raises(expected_error, match=match):
                validate_extension(mime_type, filename=filename)
        else:
            validate_extension(mime_type, filename=filename)


class TestStrategies:
    def test_base_strategy_process_is_abstract(self):
        class MockStrategy(BaseStrategy):
            def process(self, file, head):
                return super().process(file, head)

        strategy = MockStrategy()
        f = SimpleUploadedFile("test.txt", b"test content")

        with pytest.raises(NotImplementedError):
            strategy.process(f, b"test")

    def test_image_strategy_valid_image(self, file_factory):
        f = file_factory.create_real_image_file(size=(50, 30))
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
    def test_file_processor_stream_file_success(self, file_factory):
        f = file_factory.create_real_text_file()
        processor = FileProcessor(file_obj=f)

        size, head, sha256 = processor._stream_file()

        f.seek(0)
        assert size == f.size
        assert head == f.read(2048)

        f.seek(0)
        assert sha256 == hashlib.sha256(f.read()).hexdigest()

    def test_file_processor_stream_file_raises_file_too_large_error(self, file_factory):
        f = file_factory.create_mock_file(content=b"0" * (10 * 1024**2 + 1))
        processor = FileProcessor(file_obj=f)

        with pytest.raises(FileTooLargeError, match="File size exceeds the limit."):
            processor._stream_file()

    def test_file_processor_stream_file_raises_invalid_file_error_for_empty_file(self):
        f = SimpleUploadedFile("test.txt", b"")
        processor = FileProcessor(file_obj=f)

        with pytest.raises(InvalidFileError, match="Empty or broken file."):
            processor._stream_file()

    def test_file_processor_detect_mime_with_magic(self, file_factory):
        f = file_factory.create_real_pdf_file()
        processor = FileProcessor(file_obj=f, use_magic=True)
        head = f.read(2048)

        mime = processor._detect_mime(head)

        assert mime == "application/pdf"

    def test_file_processor_detect_mime_guesses_by_name(self, file_factory):
        f = file_factory.create_mock_file()
        processor = FileProcessor(file_obj=f, use_magic=False)
        head = b"dummy head"

        mime = processor._detect_mime(head)

        assert mime == "text/plain"

    def test_file_processor_detect_mime_not_allowed_type(self, file_factory):
        f = file_factory.create_mock_file(content=b"MZ...", name="app.exe")
        processor = FileProcessor(file_obj=f, use_magic=False)

        with pytest.raises(UnsupportedMimeTypeError, match="Unsupported MIME type."):
            processor._detect_mime(b"MZ head")

    def test_file_processor_detect_mime_exception_fallback(self, file_factory, mocker):
        mocker.patch(
            "apps.uploads.utils.file_processor.magic.from_buffer",
            side_effect=Exception("Simulated failure"),
        )
        f = file_factory.create_mock_file()
        processor = FileProcessor(file_obj=f, use_magic=True)
        mime = processor._detect_mime(b"some data")
        assert mime == "text/plain"

    @pytest.mark.parametrize(
        "mime_type, expected_strategy",
        [
            ("image/jpeg", ImageStrategy),
            ("application/pdf", DefaultStrategy),
            ("text/plain", DefaultStrategy),
        ],
        ids=["image", "pdf", "text"],
    )
    def test_file_processor_select_strategy_routing(self, mime_type, expected_strategy):
        processor = FileProcessor(None)
        assert isinstance(processor._select_strategy(mime_type), expected_strategy)

    def test_file_processor_process_full_flow_success(self, file_factory):
        f = file_factory.create_real_pdf_file()
        processor = FileProcessor(file_obj=f)
        result = processor.process()

        assert result["mime_type"] == "application/pdf"
        assert "hash_sha256" in result
        assert result["size"] == f.size
        assert result["original_filename"] == "test.pdf"

    def test_file_processor_process_no_file_raises_error(self):
        with pytest.raises(InvalidFileError, match="Invalid file provided."):
            FileProcessor(None).process()

    def test_file_processor_process_resets_file_pointer(self, file_factory):
        f = file_factory.create_mock_file()
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
    def test_file_processor_process_size_limits(
        self, file_factory, size_offset, expected_error
    ):
        max_size = 100
        size = max_size + size_offset
        f = file_factory.create_mock_file(content=b"0" * size)
        processor = FileProcessor(file_obj=f, max_size=max_size)

        if expected_error:
            with pytest.raises(expected_error, match="File size exceeds the limit."):
                processor.process()
        else:
            result = processor.process()
            assert result["size"] == size
