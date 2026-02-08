import io
from typing import Tuple

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

_IMAGE_FORMATS = {
    "PNG": ("image/png", "png"),
    "JPEG": ("image/jpeg", "jpg"),
    "WEBP": ("image/webp", "webp"),
    "GIF": ("image/gif", "gif"),
}
_TEXT_MIME = "text/plain"
_PDF_MIME = "application/pdf"


class FileFactory:
    """Factory for creating test files for the upload app.

    IMPORTANT:
    - mock_* methods MUST ONLY be used when FileProcessor is mocked.
    - actual_* methods generate real, valid binary content that passes
      FileProcessor validation (magic, extension, Pillow, etc.).
    """

    @staticmethod
    def create_mock_file(
        name: str = "mock.txt",
        content: bytes = b"mock content",
        content_type: str = _TEXT_MIME,
    ) -> SimpleUploadedFile:
        return SimpleUploadedFile(name, content, content_type)

    @staticmethod
    def create_real_image_file(
        format: str = "PNG",
        size: Tuple[int, int] = (64, 64),
        name: str | None = None,
    ) -> SimpleUploadedFile:
        mime, ext = _IMAGE_FORMATS[format]
        filename = name or f"test_image.{ext}"

        buffer = io.BytesIO()
        mode = "P" if format == "GIF" else "RGB"
        image = Image.new(mode, size)
        image.save(buffer, format=format)
        buffer.seek(0)

        return SimpleUploadedFile(filename, buffer.read(), mime)

    @staticmethod
    def create_real_text_file(
        name: str = "test.txt",
        content: bytes = b"valid text content\n",
    ) -> SimpleUploadedFile:
        return SimpleUploadedFile(name, content, _TEXT_MIME)

    def create_real_pdf_file(name: str = "test.pdf") -> SimpleUploadedFile:
        content = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
            b"xref\n0 1\n0000000000 65535 f\n"
            b"trailer\n<< /Root 1 0 R >>\n"
            b"startxref\n0\n%%EOF\n"
        )
        return SimpleUploadedFile(name, content, _PDF_MIME)
