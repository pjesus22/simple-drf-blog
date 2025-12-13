from pytest_factoryboy import register
from tests.factories import (
    AdminFactory,
    EditorFactory,
    ProfileFactory,
    SocialLinkFactory,
)

register(EditorFactory)
register(ProfileFactory)
register(AdminFactory)
register(SocialLinkFactory)
