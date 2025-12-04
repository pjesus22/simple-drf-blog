import factory
from apps.uploads.models import Upload
from django.core.files.base import ContentFile


class UploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    uploaded_by = factory.SubFactory("tests.factories.users_factories.EditorFactory")
    purpose = "test"

    @factory.lazy_attribute
    def file(self):
        content = ContentFile(b"Fake file content", name="test.txt")
        return content
