from abc import ABC, abstractmethod
import hashlib
import logging
import mimetypes
import os
from typing import Any, BinaryIO

from django.utils.text import get_valid_filename
import magic
from PIL import Image, UnidentifiedImageError

from apps.uploads.exceptions import (
    FileTooLargeError,
    InvalidFileError,
    UnsupportedMimeTypeError,
    UploadDomainError,
)

logger = logging.getLogger(__name__)

ALLOWED_MIME_EXTENSIONS = {
    "image/jpeg": {"jpg", "jpeg"},
    "image/png": {"png"},
    "image/gif": {"gif"},
    "image/webp": {"webp"},
    "application/pdf": {"pdf"},
    "text/plain": {"txt"},
    "video/mp4": {"mp4"},
    "audio/mpeg": {"mp3"},
}


def validate_extension(mime: str, filename: str) -> None:
    ext = os.path.splitext(filename)[1].lstrip(".").lower()

    if not ext:
        raise InvalidFileError("Uploaded file has no extension.")

    allowed = ALLOWED_MIME_EXTENSIONS.get(mime)

    if not allowed:
        raise UnsupportedMimeTypeError(f"MIME type '{mime}' is not allowed.")

    if ext not in allowed:
        raise InvalidFileError(
            f"File extension '.{ext}' is not allowed for MIME type '{mime}'."
        )


class BaseStrategy(ABC):
    @abstractmethod
    def process(self, file: BinaryIO, head: bytes) -> dict[str, Any]:
        raise NotImplementedError


class ImageStrategy(BaseStrategy):
    def process(self, file: BinaryIO, head: bytes) -> dict[str, Any]:
        try:
            with Image.open(file) as img:
                img.verify()

            file.seek(0)
            with Image.open(file) as img:
                width, height = img.size

            return {"width": width, "height": height}
        except (UnidentifiedImageError, OSError):
            raise InvalidFileError(
                "Uploaded file is not a valid or supported image."
            ) from None


class DefaultStrategy(BaseStrategy):
    def process(self, file: BinaryIO, head: bytes) -> dict[str, Any]:
        return {}


class FileProcessor:
    DEFAULT_MAX_SIZE = 10 * 1024**2  # 10MiB
    IMAGE_STRATEGY = ImageStrategy()
    DEFAULT_STRATEGY = DefaultStrategy()

    def __init__(
        self,
        file_obj: BinaryIO,
        file_name: str | None = None,
        max_size: int | None = None,
        use_magic: bool = True,
    ):
        self.file = file_obj
        self.file_name = file_name or getattr(file_obj, "name", "")
        self.use_magic = use_magic
        self.max_size = max_size or self.DEFAULT_MAX_SIZE

    def _stream_file(self, chunk_size: int = 8192) -> tuple[int, bytes, str]:
        """Streams the file once:
        - Computes SHA-256
        - Captures head bytes
        - Computes size
        """
        hasher = hashlib.sha256()
        size = 0
        head = b""

        self.file.seek(0)

        for chunk in iter(lambda: self.file.read(chunk_size), b""):
            if size < 2048:
                head += chunk[: 2048 - size]
            size += len(chunk)
            hasher.update(chunk)

        if size > self.max_size:
            raise FileTooLargeError()

        if size == 0:
            raise InvalidFileError("Empty or broken file.")

        return size, head, hasher.hexdigest()

    def _detect_mime(self, head: bytes) -> str:
        mime = None

        if self.use_magic:
            try:
                mime = magic.from_buffer(head, mime=True)
            except Exception as exc:
                logger.warning("Magic MIME detection failed: %s", exc)

        if not mime:
            guessed, _ = mimetypes.guess_type(self.file_name)
            mime = guessed

        mime = (mime or "application/octet-stream").lower()

        if mime not in ALLOWED_MIME_EXTENSIONS:
            raise UnsupportedMimeTypeError()

        return mime

    def _select_strategy(self, mime: str) -> BaseStrategy:
        if mime.startswith("image/"):
            return self.IMAGE_STRATEGY
        return self.DEFAULT_STRATEGY

    def process(self) -> dict[str, Any]:
        if not self.file:
            raise InvalidFileError()

        try:
            size, head, sha256 = self._stream_file()
            mime = self._detect_mime(head)

            validate_extension(mime, self.file_name)

            strategy = self._select_strategy(mime)

            self.file.seek(0)
            base_meta = strategy.process(self.file, head)

            return {
                "mime_type": mime,
                "hash_sha256": sha256,
                "size": size,
                "original_filename": get_valid_filename(
                    os.path.basename(self.file_name)
                ),
                **base_meta,
            }
        except UploadDomainError:
            raise
        finally:
            self.file.seek(0)
