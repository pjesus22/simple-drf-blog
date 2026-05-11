from django.db import IntegrityError, models
import pytest

from apps.content.mixins import SlugMixin

pytestmark = pytest.mark.django_db


class MockModel(SlugMixin):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    class Meta:
        app_label = "content"


class TestSlugMixin:
    def test_get_slug_field(self):
        mock_model = MockModel()
        result = mock_model._get_slug_field()
        assert result == "slug"

    def test_get_slug_source_value(self):
        mock_model = MockModel(title="test")
        result = mock_model._get_slug_source_value()
        assert result == "test"

    @pytest.mark.parametrize(
        "create_conflict, expected", [(True, True), (False, False)]
    )
    def test_slug_exists(self, post_factory, create_conflict, expected):
        if create_conflict:
            post_factory(title="test")
        post = post_factory.build(slug="test")
        assert post._slug_exists(post.slug) == expected

    def test_slug_exists_excludes_self(self, post_factory):
        post = post_factory(title="test")
        assert not post._slug_exists(post.slug)

    def test_generate_base_slug(self):
        mock_model = MockModel(title="test")
        result = mock_model._generate_base_slug()
        assert result == "test"

    def test_generate_unique_slug(self, post_factory):
        post_factory(title="test", slug="test")
        post = post_factory.build(title="test", slug="test")
        result = post._generate_unique_slug()
        assert result == "test-1"

    def test_set_slug(self, post_factory):
        post_factory(title="test")
        post = post_factory.build(slug="test")
        post._set_slug()
        assert post.slug == "test"

    def test_set_slug_generates_from_title_when_slug_is_none(self, post_factory):
        post = post_factory.build(title="test", slug=None)
        post._set_slug()
        assert post.slug == "test"

    def test_save_retries_on_integrity_error(
        self, post_factory, monkeypatch, editor_factory, category_factory
    ):
        editor = editor_factory()
        category = category_factory()
        post = post_factory.build(title="test", category=category, author=editor)
        retries = []
        original_save = models.Model.save

        def flaky_model_save(instance, *args, **kwargs):
            retries.append(True)
            if len(retries) == 1:
                raise IntegrityError("Simulated race condition")
            return original_save(instance, *args, **kwargs)

        monkeypatch.setattr(models.Model, "save", flaky_model_save)

        post.save()

        assert len(retries) == 2
        assert post.pk is not None

    def test_save_raises_exception_after_max_retries(self, post_factory, monkeypatch):
        post = post_factory.build(title="test")

        def always_fail(*args, **kwargs):
            raise IntegrityError("Simulated race condition")

        monkeypatch.setattr(models.Model, "save", always_fail)

        with pytest.raises(
            IntegrityError, match="Could not generate a unique slug after retries"
        ):
            post.save()
