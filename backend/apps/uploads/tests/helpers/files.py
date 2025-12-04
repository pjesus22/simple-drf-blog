import io
from typing import Tuple

from PIL import Image


def make_file(content: bytes, name: str = "file.bin"):
    f = io.BytesIO(content)
    f.name = name
    return f


def make_image(format: str = "PNG", size: Tuple[int, int] = (50, 30), filename=None):
    filename = filename or f"test.{format.lower()}"
    tmp = io.BytesIO()

    img = Image.new("RGB", size)
    img.save(fp=tmp, format=format)

    tmp.seek(0)
    tmp.name = filename
    return tmp
