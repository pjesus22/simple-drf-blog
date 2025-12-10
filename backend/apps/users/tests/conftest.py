from pytest_factoryboy import register
from tests.factories import AdminFactory, EditorFactory, ProfileFactory

register(EditorFactory)
register(ProfileFactory)
register(AdminFactory)
