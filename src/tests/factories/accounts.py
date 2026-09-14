import uuid

import factory

from apps.accounts.models import User

from .profiles import ProfileFactory


class BaseUserFactory(factory.django.DjangoModelFactory):
    username = factory.LazyFunction(lambda: f"user_{uuid.uuid4().hex[:12]}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.django.Password("defaultpassword")

    class Meta:
        abstract = True
        skip_postgeneration_save = True


class DefaultUserFactory(BaseUserFactory):
    class Meta:
        model = "accounts.User"


class AdminFactory(BaseUserFactory):
    role = User.Role.ADMIN

    class Meta:
        model = "accounts.Admin"


class EditorFactory(BaseUserFactory):
    role = User.Role.EDITOR

    class Meta:
        model = "accounts.Editor"

    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        if extracted is True:
            ProfileFactory(user=self)
