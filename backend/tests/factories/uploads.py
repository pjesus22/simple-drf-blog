import hashlib
import uuid

import factory
from apps.uploads.models import Upload
from django.core.files.base import ContentFile


class UploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    uploaded_by = factory.SubFactory("tests.factories.accounts.EditorFactory")
    mime_type = "text/plain"
    purpose = Upload.Purpose.ATTACHMENT
    visibility = Upload.Visibility.INHERIT

    @factory.lazy_attribute
    def file(self):
        unique_id = uuid.uuid4().hex
        return ContentFile(
            f"Fake content for {unique_id}".encode(),
            name=f"file_{unique_id}.txt",
        )

    @factory.lazy_attribute
    def original_filename(self):
        return self.file.name

    @factory.lazy_attribute
    def size(self):
        return self.file.size

    @factory.lazy_attribute
    def hash_sha256(self):
        content = self.file.open().read()
        self.file.seek(0)
        return hashlib.sha256(content).hexdigest()
