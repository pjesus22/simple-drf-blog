import os
from typing import Optional

from apps.uploads.models import Upload
from apps.users.models import User
from django.core.exceptions import FieldDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.db import models


def attach_upload(
    instance: models.Model,
    file: UploadedFile,
    field_name: str,
    subdir: Optional[str] = None,
    uploaded_by: Optional[User] = None,
    purpose: Optional[str] = None,
):
    """
    Attach a file to an Upload field in a model instance.

    Create a record in the `Upload` model, define the dynamic subdirectory
    based on `purpose` or `subdir`, and associate the file with the
    specified field in the model.

    Args:
        instance (models.Model): Model instance where the file will be attached.
        file (UploadedFile): Uploaded file (e.g., from a form or API).
        field_name (str): Name of the field that will receive the relationship with Upload.
        subdir (str): Optional subdirectory to store the file.
        uploaded_by (User): User performing the upload (can be None).
        purpose (str): Purpose of the file, used to define the logical folder.

    Returns:
        Upload: Created instance of the Upload model.

    Raises:
        FieldDoesNotExist: If the `field_name` field does not exist in the model.
        ValueError: If the field is not compatible with Upload.
    """
    try:
        field = instance._meta.get_field(field_name)
    except FieldDoesNotExist as exc:
        raise FieldDoesNotExist(
            f"The model{instance.__class__.__name__} doesn't have a '{field_name}'."
        ) from exc

    date_path = "%Y%m%d"
    filename = os.path.basename(file.name)
    final_subdir = subdir or purpose or "uploads"
    file.name = os.path.join(final_subdir, date_path, filename)

    upload = Upload.objects.create(
        file=file,
        uploaded_by=uploaded_by,
        purpose=purpose,
    )

    if field.many_to_many:
        getattr(instance, field_name).add(upload)
    elif isinstance(field, models.ForeignKey) or isinstance(
        field, models.OneToOneField
    ):
        setattr(instance, field_name, upload)
        instance.save()
    else:
        raise ValueError(
            f"The field '{field_name}' in {instance.__class__.__name__} is not a valid relationship with Upload."
        )
    return upload
