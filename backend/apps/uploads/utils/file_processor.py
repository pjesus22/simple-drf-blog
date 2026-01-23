import hashlib
import logging
import mimetypes
import os
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, Dict, Optional

import magic
from apps.uploads.exceptions import (
    FileTooLargeError,
    InvalidFileError,
    UnsupportedMimeTypeError,
    UploadError,
)
from django.utils.text import get_valid_filename
from PIL import Image, UnidentifiedImageError

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

DENIED_MIME_TYPES = {
    "application/x-msdownload",
    "application/x-executable",
    "application/x-sh",
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
                width, height = img.size
            return {"file_type": "image", "width": width, "height": height}
        except (UnidentifiedImageError, OSError):
            raise InvalidFileError("Uploaded file is not a valid or supported image.")


class DefaultStrategy(BaseStrategy):
    def process(self, file: BinaryIO, head: bytes) -> dict[str, Any]:
        return {"file_type": "other"}


class FileProcessor:
    DEFAULT_MAX_SIZE = 10 * 1024**2  # 10MiB
    IMAGE_STRATEGY = ImageStrategy()
    DEFAULT_STRATEGY = DefaultStrategy()

    def __init__(
        self,
        file_obj: BinaryIO,
        file_name: Optional[str] = None,
        max_size: Optional[int] = None,
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
            raise FileTooLargeError("The file exceeds the maximum size permitted.")

        if size == 0:
            raise InvalidFileError("Empty or broken file.")

        return size, head, hasher.hexdigest()

    def _detect_mime(self, head: bytes) -> str:
        try:
            mime = None

            if self.use_magic:
                mime = magic.from_buffer(head, mime=True)

            if not mime:
                guessed, _ = mimetypes.guess_type(self.file_name)
                mime = guessed

            mime = (mime or "application/octet-stream").lower()

            if mime in DENIED_MIME_TYPES:
                raise UnsupportedMimeTypeError(f"MIME type '{mime}' is not allowed.")

            return mime

        except UploadError:
            raise
        except Exception as exc:
            logger.warning("MIME detection failed: %s", exc)
            return "application/octet-stream"

    def _select_strategy(self, mime: str) -> BaseStrategy:
        if mime.startswith("image/"):
            return self.IMAGE_STRATEGY
        return self.DEFAULT_STRATEGY

    def process(self) -> Dict[str, Any]:
        if not self.file:
            raise InvalidFileError("No file provided.")

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
                    os.path.basename(self.file.name)
                ),
                **base_meta,
            }
        except UploadError:
            raise
        finally:
            self.file.seek(0)
