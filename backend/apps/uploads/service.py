from django.core.exceptions import ValidationError
from django.db.models import Model
from utils.file_tools import FileProcessor


class UploadService:
    @staticmethod
    def update_metadata(instance: Model) -> None:
        """
        Processes the file associated with the given instance and
        updates its metadata.

        Args:
            instance (Upload): Model instance with a `file` field. Expected to
            contain attributes such as:
                - mime_type
                - hash_md5
                - size
                - original_filename
                - file_type
                - (optional) width, height

        Raises:
            `ValidationError`: If no file is provided or if an error
            occurs during file processing.
        """

        if not getattr(instance, "file", None):
            raise ValidationError("No file provided for metadata extraction.")

        try:
            processor = FileProcessor(
                file_obj=instance.file,
                file_name=instance.file.name,
            )
            meta = processor.process()

            instance.mime_type = meta["mime_type"]
            instance.hash_md5 = meta["hash_md5"]
            instance.size = meta["size"]
            instance.original_filename = meta["original_filename"]
            instance.file_type = meta["file_type"]

            if "width" in meta:
                instance.width = meta["width"]
                instance.height = meta["height"]

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Unexpected error processing file: {e}")
