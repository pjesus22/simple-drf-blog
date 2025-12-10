import hashlib
import logging
import mimetypes
import os
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, Dict, Optional

import magic
from django.core.exceptions import ValidationError
from django.utils.text import get_valid_filename
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    @abstractmethod
    def process(self, file: BinaryIO, head: Optional[bytes] = None) -> dict[str, Any]:
        pass


class ImageStrategy(BaseStrategy):
    def process(self, file: BinaryIO, head: Optional[bytes] = None) -> dict[str, Any]:
        try:
            with Image.open(file) as img:
                img.verify()
                width, height = img.size
            file.seek(0)
            return {"file_type": "image", "width": width, "height": height}
        except (UnidentifiedImageError, OSError):
            raise ValidationError("Uploaded file is not a valid or supported image.")


class VideoStrategy(BaseStrategy):
    def process(self, file: BinaryIO, head: Optional[bytes] = None) -> dict[str, Any]:
        # TODO: Add video processing metadata.
        # HINT: Could use moviepy or ffmpeg here in the future
        return {"file_type": "video"}


class AudioStrategy(BaseStrategy):
    def process(self, file: BinaryIO, head: Optional[bytes] = None) -> dict[str, Any]:
        return {"file_type": "audio"}


class DocumentStrategy(BaseStrategy):
    def process(self, file: BinaryIO, head: Optional[bytes] = None) -> dict[str, Any]:
        return {"file_type": "document"}


class DefaultStrategy(BaseStrategy):
    def process(self, file: BinaryIO, head: Optional[bytes] = None) -> dict[str, Any]:
        return {"file_type": "other"}


class FileProcessor:
    STRATEGIES = {
        "image/": ImageStrategy(),
        "video/": VideoStrategy(),
        "audio/": AudioStrategy(),
        "application/": DocumentStrategy(),
    }

    def __init__(
        self,
        file_obj: BinaryIO,
        file_name: Optional[str] = None,
        use_magic: bool = True,
        max_size: Optional[int] = None,
    ):
        self.file: BinaryIO = file_obj
        self.file_name: str = file_name or getattr(file_obj, "name", "")
        self.use_magic: bool = use_magic
        self._head: Optional[bytes] = None
        self.mime_type: Optional[str] = None
        self.strategy: BaseStrategy = DefaultStrategy()
        self.MAX_FILE_SIZE = max_size or 10 * 1024**2

    def _read_head(self, bytes_count: int = 2048) -> bytes:
        data = self.file.read(bytes_count) or b""
        self._head = data
        self.file.seek(0)
        return data

    def detect_mime_type(self) -> None:
        data = self._head or self._read_head()
        try:
            if self.use_magic:
                mime = magic.from_buffer(data, mime=True)
            else:
                mime = None

            if not mime:
                guessed, _ = mimetypes.guess_type(self.file_name)
                mime = guessed

            self.mime_type = mime or "application/octet-stream"
        except Exception as exc:
            logger.warning(f"MIME detection failed for {self.file_name}: {exc}")
            self.mime_type = "application/octet-stream"

    def select_strategy(self) -> BaseStrategy:
        if not self.mime_type:
            self.detect_mime_type()

        mime = (self.mime_type or "application/octet-stream").lower()
        for prefix, strategy in self.STRATEGIES.items():
            if mime.startswith(prefix):
                self.strategy = strategy
                break
        return self.strategy

    def compute_md5(self, chunk_size: int = 8192) -> str:
        md5 = hashlib.md5()
        self.file.seek(0)
        for chunk in iter(lambda: self.file.read(chunk_size), b""):
            md5.update(chunk)
        self.file.seek(0)
        return md5.hexdigest().lower()

    def _get_size(self) -> int:
        if hasattr(self.file, "size"):
            return self.file.size
        try:
            self.file.seek(0, os.SEEK_END)
            size = self.file.tell()
            self.file.seek(0)
            if size <= 0:
                raise ValidationError("Empty or broken file.")
            return size
        except Exception as e:
            raise ValidationError(f"Could not determine file size: {e}")

    def process(self) -> Dict[str, Any]:
        if not self.file:
            raise ValidationError("No file provided.")

        size = self._get_size()

        if size > self.MAX_FILE_SIZE:
            raise ValidationError("The file exceeds the maximum size permitted.")

        head = self._read_head()
        self.detect_mime_type()
        self.select_strategy()

        base_meta = self.strategy.process(self.file, head)
        hash_md5 = self.compute_md5()
        original_filename = get_valid_filename(os.path.basename(self.file_name))

        return {
            "mime_type": self.mime_type,
            "hash_md5": hash_md5,
            "size": size,
            "original_filename": original_filename,
            **base_meta,
        }

        # TODO: Extension/actual-type validation. Make a validator to verify
        # that the file extension matches the detected MIME type.
        # This prevents uploads with false extensions (e.g. .jpg with .exe
        # content).
