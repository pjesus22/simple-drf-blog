from apps.content.models import Category, Post, Tag
from apps.users.models import Editor


class TestCategoryModel:
    def test_category_str_returns_name(self):
        category = Category(name="Test Category")
        assert str(category) == "Test Category"

    def test_category_clean_generates_slug(self, db):
        category = Category(name="Test Category")
        category.clean()
        assert category.slug == "test-category"

    def test_create_category(self, db):
        category = Category.objects.create(
            name="Test Category", description="A test category"
        )
        assert category.id is not None


class TestTagModel:
    def test_tag_str_returns_name(self):
        tag = Tag(name="Test Tag")
        assert str(tag) == "Test Tag"

    def test_tag_clean_generates_slug(self, db):
        tag = Tag(name="Test Tag")
        tag.clean()
        assert tag.slug == "test-tag"

    def test_create_tag(self, db):
        tag = Tag.objects.create(name="Test Tag")
        assert tag.id is not None


class TestPostModel:
    def test_post_str_returns_title(self):
        post = Post(title="Test Post")
        assert str(post) == "Test Post"

    def test_post_clean_generates_slug(self, db):
        post = Post(title="Test Post")
        post.clean()
        assert post.slug == "test-post"

    def test_post_clean_sets_published_at(self, db):
        post = Post(title="Test Post", status=Post.Status.PUBLISHED)
        post.clean()
        assert post.published_at is not None

    def test_create_post(self, db):
        category = Category.objects.create(name="Test Category")
        author = Editor.objects.create(
            username="testeditor",
            email="fake_email@example.com",
            first_name="Test",
            last_name="Editor",
        )
        post = Post.objects.create(title="Test Post", category=category, author=author)
        assert post.id is not None

    def test_status_methods(self):
        post = Post(title="Test Post", status=Post.Status.PUBLISHED)
        assert post.is_published() is True
        assert post.is_draft() is False
        assert post.is_archived() is False
        assert post.is_deleted() is False
