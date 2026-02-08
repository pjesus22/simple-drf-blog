from pytest_factoryboy import register
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
