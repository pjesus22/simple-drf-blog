from utils.text_tools import generate_slug

from apps.content.models import Category


def test_generate_slug_deduplicates_same_slug(db):
    category = Category.objects.create(
        name="Test Category", description="Common test category"
    )
    slug = generate_slug(instance=category, field_value=category.name)

    assert category.slug != slug
