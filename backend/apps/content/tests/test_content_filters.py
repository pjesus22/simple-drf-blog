import pytest
from apps.content.filters import PostFilter
from apps.content.models import Post

pytestmark = pytest.mark.django_db


class TestPostFilter:
    def test_category_filter_success(self, category_factory, post_factory):
        tech_category = category_factory(slug="technology")
        news_category = category_factory(slug="news")

        tech_post = post_factory(category=tech_category, status=Post.Status.PUBLISHED)
        news_post = post_factory(category=news_category, status=Post.Status.PUBLISHED)

        filterset = PostFilter(
            data={"category": "technology"}, queryset=Post.objects.all()
        )
        results = filterset.qs

        assert results.count() == 1
        assert tech_post in results
        assert news_post not in results

    @pytest.mark.parametrize(
        "query_tags, expected_count, included_indices",
        [
            ("python", 2, [0, 2]),
            ("django", 1, [0]),
            ("python,django", 2, [0, 2]),
            ("python, django ", 2, [0, 2]),
            ("nonexistent", 0, []),
        ],
        ids=["python", "django", "python,django", "python, django ", "nonexistent"],
    )
    def test_tags_filter(
        self, tag_factory, post_factory, query_tags, expected_count, included_indices
    ):
        python_tag = tag_factory(slug="python")
        django_tag = tag_factory(slug="django")
        javascript_tag = tag_factory(slug="javascript")

        posts = [
            post_factory(status=Post.Status.PUBLISHED),
            post_factory(status=Post.Status.PUBLISHED),
            post_factory(status=Post.Status.PUBLISHED),
        ]
        posts[0].tags.set([python_tag, django_tag])
        posts[1].tags.set([javascript_tag])
        posts[2].tags.set([python_tag])

        filterset = PostFilter(data={"tags": query_tags}, queryset=Post.objects.all())
        results = filterset.qs

        assert results.count() == expected_count
        for i in included_indices:
            assert posts[i] in results

        included_set = set(included_indices)
        for i, post in enumerate(posts):
            if i not in included_set:
                assert post not in results

    @pytest.mark.parametrize(
        "search_term, expected_titles",
        [
            ("Django", ["Django Tutorial", "Python Patterns in Django"]),
            ("Beginners", ["Django Tutorial"]),
            ("Decorators", ["Python Patterns in Django"]),
            ("JavaScript", ["JavaScript Fundamentals"]),
            ("NonExistent", []),
        ],
        ids=["django", "beginners", "decorators", "javascript", "nonexistent"],
    )
    def test_search_filter(self, post_factory, search_term, expected_titles):
        post_factory(
            title="Django Tutorial",
            content="Learn Django for Beginners",
            status=Post.Status.PUBLISHED,
        )
        post_factory(
            title="Python Patterns in Django",
            content="Decorators and more",
            status=Post.Status.PUBLISHED,
        )
        post_factory(
            title="JavaScript Fundamentals",
            content="Basic JS",
            status=Post.Status.PUBLISHED,
        )

        filterset = PostFilter(
            data={"search": search_term}, queryset=Post.objects.all()
        )

        results = filterset.qs
        assert results.count() == len(expected_titles)

        result_titles = [post.title for post in results]
        for title in expected_titles:
            assert title in result_titles

    def test_combined_filters(self, category_factory, tag_factory, post_factory):
        tech_category = category_factory(slug="technology")
        news_category = category_factory(slug="news")
        python_tag = tag_factory(slug="python")

        post1 = post_factory(
            title="Python AI", category=tech_category, status=Post.Status.PUBLISHED
        )
        post1.tags.set([python_tag])

        post_factory(
            title="Tech News", category=tech_category, status=Post.Status.PUBLISHED
        )

        post3 = post_factory(
            title="Python Journalism",
            category=news_category,
            status=Post.Status.PUBLISHED,
        )
        post3.tags.set([python_tag])

        filterset = PostFilter(
            data={"category": "technology", "tags": "python"},
            queryset=Post.objects.all(),
        )
        assert filterset.qs.count() == 1
        assert post1 in filterset.qs

        filterset = PostFilter(
            data={"category": "technology", "search": "Python"},
            queryset=Post.objects.all(),
        )
        assert filterset.qs.count() == 1
        assert post1 in filterset.qs

    def test_filter_reflects_all_statuses(self, category_factory, post_factory):
        category = category_factory(slug="test")
        p1 = post_factory(category=category, status=Post.Status.PUBLISHED)
        p2 = post_factory(category=category, status=Post.Status.DRAFT)
        p3 = post_factory(category=category, status=Post.Status.ARCHIVED)

        filterset = PostFilter(data={"category": "test"}, queryset=Post.objects.all())
        assert filterset.qs.count() == 3
        assert p1 in filterset.qs
        assert p2 in filterset.qs
        assert p3 in filterset.qs

    @pytest.mark.parametrize(
        "empty_data",
        [
            {},
            {"category": ""},
            {"tags": ""},
            {"search": ""},
            {"category": "", "tags": "", "search": ""},
        ],
        ids=("empty_data", "category_empty", "tags_empty", "search_empty", "all_empty"),
    )
    def test_empty_filters_return_all(self, post_factory, empty_data):
        post_factory.create_batch(3, status=Post.Status.PUBLISHED)

        filterset = PostFilter(data=empty_data, queryset=Post.objects.all())
        assert filterset.qs.count() == 3
