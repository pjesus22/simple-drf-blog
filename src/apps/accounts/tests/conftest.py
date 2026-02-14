import pytest
from pytest_factoryboy import register
from rest_framework.fields import DateTimeField

from tests.factories import (
    AdminFactory,
    DefaultUserFactory,
    EditorFactory,
    ProfileFactory,
    SocialMediaProfileFactory,
)

register(DefaultUserFactory)
register(EditorFactory)
register(ProfileFactory)
register(AdminFactory)
register(SocialMediaProfileFactory)


@pytest.fixture
def drf_datetime():
    return DateTimeField()
