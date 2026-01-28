from pytest_factoryboy import register
from tests.factories import (
    AdminFactory,
    DefaultUserFactory,
    EditorFactory,
    ProfileFactory,
    SocialLinkFactory,
)

register(DefaultUserFactory)
register(EditorFactory)
register(ProfileFactory)
register(AdminFactory)
register(SocialLinkFactory)
