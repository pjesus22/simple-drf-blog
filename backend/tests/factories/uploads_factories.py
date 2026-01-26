import factory
from apps.uploads.models import Upload
from django.core.files.base import ContentFile


class UploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    uploaded_by = factory.SubFactory("tests.factories.accounts.EditorFactory")
    purpose = factory.Faker("random_element", elements=Upload.Purpose.values)
    original_filename = factory.Faker("file_name")
    mime_type = "text/plain"
    hash_sha256 = factory.Faker("hexify", text="^" * 64)
    size = 1024
    visibility = Upload.Visibility.INHERIT

    @factory.lazy_attribute
    def file(self):
        content = ContentFile(b"Fake file content", name="test.txt")
        return content
