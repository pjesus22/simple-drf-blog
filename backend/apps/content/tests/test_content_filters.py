import pytest
from apps.content.filters import PostFilter
from apps.content.models import Post

pytestmark = pytest.mark.django_db


class TestPostFilter:
    def test_category_filter_success(self, category_factory, post_factory):
        tech_category = category_factory(name="Technology")
        news_category = category_factory(name="News")
        sports_category = category_factory(name="Sports")

        tech_post = post_factory(
            title="AI Advancements",
            category=tech_category,
            status=Post.Status.PUBLISHED,
        )
        news_post = post_factory(
            title="Breaking News",
            category=news_category,
            status=Post.Status.PUBLISHED,
        )
        sports_post = post_factory(
            title="World Cup Final",
            category=sports_category,
            status=Post.Status.PUBLISHED,
        )

        filterset = PostFilter(
            data={"category": "technology"}, queryset=Post.objects.all()
        )
        results = filterset.qs

        assert results.count() == 1
        assert tech_post in results
        assert news_post not in results
        assert sports_post not in results

    def test_tags_filter_success(self, tag_factory, post_factory):
        python_tag = tag_factory(name="Python")
        django_tag = tag_factory(name="Django")
        javascript_tag = tag_factory(name="JavaScript")

        post1 = post_factory(status=Post.Status.PUBLISHED)
        post1.tags.set([python_tag, django_tag])

        post2 = post_factory(status=Post.Status.PUBLISHED)
        post2.tags.set([javascript_tag])

        post3 = post_factory(status=Post.Status.PUBLISHED)
        post3.tags.set([python_tag, javascript_tag])

        # Test filtering by single tag
        filterset = PostFilter(data={"tags": "python"}, queryset=Post.objects.all())
        results = filterset.qs

        assert results.count() == 2
        assert post1 in results
        assert post2 not in results
        assert post3 in results

        # Test filtering by multiple tags (comma-separated)
        filterset = PostFilter(
            data={"tags": "python,django"}, queryset=Post.objects.all()
        )
        results = filterset.qs

        assert results.count() == 2
        assert post1 in results
        assert post2 not in results
        assert post3 in results

    def test_search_filter_success(self, post_factory):
        # Create posts with different titles and content
        post1 = post_factory(
            title="Django Tutorial for Beginners",
            content="Learn Django step by step",
            status=Post.Status.PUBLISHED,
        )
        post2 = post_factory(
            title="Advanced Python Patterns",
            content="Decorators, generators, and context managers in Django projects",
            status=Post.Status.PUBLISHED,
        )
        post3 = post_factory(
            title="JavaScript Fundamentals",
            content="Basic JavaScript concepts",
            status=Post.Status.PUBLISHED,
        )

        # Test search in title (partial match)
        filterset = PostFilter(data={"search": "Django"}, queryset=Post.objects.all())
        results = filterset.qs

        assert results.count() == 2  # post1 and post2
        assert post1 in results
        assert post2 in results
        assert post3 not in results

        # Test search in content
        filterset = PostFilter(data={"search": "step"}, queryset=Post.objects.all())
        results = filterset.qs

        assert results.count() == 1
        assert post1 in results
        assert post2 not in results
        assert post3 not in results

        # Test search that matches both title and content in different posts
        filterset = PostFilter(data={"search": "Python"}, queryset=Post.objects.all())
        results = filterset.qs

        assert results.count() == 1
        assert post2 in results

    def test_combined_filters(self, category_factory, tag_factory, post_factory):
        tech_category = category_factory(slug="technology")
        news_category = category_factory(slug="news")
        python_tag = tag_factory(slug="python")
        ai_tag = tag_factory(slug="ai")

        # Post 1: Tech category, Python tag
        post1 = post_factory(
            title="Python AI Development",
            content="Using Python for AI projects",
            category=tech_category,
            status=Post.Status.PUBLISHED,
        )
        post1.tags.set([python_tag, ai_tag])

        # Post 2: Tech category, no Python tag
        post2 = post_factory(
            title="General Technology News",
            content="Latest in tech",
            category=tech_category,
            status=Post.Status.PUBLISHED,
        )

        # Post 3: News category, Python tag
        post3 = post_factory(
            title="Python in Journalism",
            content="News about Python",
            category=news_category,
            status=Post.Status.PUBLISHED,
        )
        post3.tags.set([python_tag])

        # Test combined filter: category=technology AND tags=python
        filterset = PostFilter(
            data={"category": "technology", "tags": "python"},
            queryset=Post.objects.all(),
        )
        results = filterset.qs

        assert results.count() == 1
        assert post1 in results
        assert post2 not in results
        assert post3 not in results

        # Test combined filter: category=technology AND search=Python
        filterset = PostFilter(
            data={"category": "technology", "search": "Python"},
            queryset=Post.objects.all(),
        )
        results = filterset.qs

        assert results.count() == 1
        assert post1 in results
        assert post2 not in results
        assert post3 not in results

    def test_filter_with_different_post_statuses(self, category_factory, post_factory):
        category = category_factory(slug="test-category")
        published_post = post_factory(
            title="Published Post", category=category, status=Post.Status.PUBLISHED
        )
        draft_post = post_factory(
            title="Draft Post", category=category, status=Post.Status.DRAFT
        )
        archived_post = post_factory(
            title="Archived Post", category=category, status=Post.Status.ARCHIVED
        )

        filterset = PostFilter(
            data={"category": "test-category"}, queryset=Post.objects.all()
        )
        results = filterset.qs

        assert results.count() == 3
        assert published_post in results
        assert draft_post in results
        assert archived_post in results

    def test_empty_filters_return_all(self, post_factory):
        post_factory.create_batch(3, status=Post.Status.PUBLISHED)

        filterset = PostFilter(data={}, queryset=Post.objects.all())
        results = filterset.qs

        assert results.count() == 3

        # Test with empty string values
        filterset = PostFilter(
            data={"category": "", "tags": "", "search": ""}, queryset=Post.objects.all()
        )
        results = filterset.qs

        assert results.count() == 3
