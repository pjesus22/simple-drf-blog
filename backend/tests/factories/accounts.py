import factory
from apps.accounts.models import User
from faker import Faker

from .profiles import ProfileFactory

_fake = Faker()


class BaseUserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    password = factory.django.Password("defaultpassword")

    class Meta:
        abstract = True
        django_get_or_create = ("username",)
        skip_postgeneration_save = True


class DefaultUserFactory(BaseUserFactory):
    class Meta:
        model = "accounts.User"

    @factory.post_generation
    def finalize(self, create, extracted, **kwargs):
        if create:
            if self.role == User.Role.ADMIN:
                self.is_staff = True
                self.is_superuser = True
            else:
                self.is_staff = False
                self.is_superuser = False
            self.save(update_fields=["is_staff", "is_superuser"])


class AdminFactory(BaseUserFactory):
    role = User.Role.ADMIN

    class Meta:
        model = "accounts.Admin"

    @factory.post_generation
    def finalize(self, create, extracted, **kwargs):
        if create and self.role == User.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
            self.save(update_fields=["is_staff", "is_superuser"])


class EditorFactory(BaseUserFactory):
    role = User.Role.EDITOR

    class Meta:
        model = "accounts.Editor"

    @factory.post_generation
    def finalize(self, create, extracted, **kwargs):
        if create and self.role == User.Role.EDITOR:
            self.is_staff = False
            self.is_superuser = False
            self.save(update_fields=["is_staff", "is_superuser"])

    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        if extracted is True:
            ProfileFactory(user=self)
