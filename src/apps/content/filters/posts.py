import django_filters

from apps.content.models import Post


class PostFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name="category__slug", lookup_expr="iexact"
    )
    tags = django_filters.CharFilter(method="filter_tags")

    class Meta:
        model = Post
        fields = ["category", "tags"]

    def filter_tags(self, queryset, name, value):
        tag_slugs = [v.strip() for v in value.split(",")]
        return queryset.filter(tags__slug__in=tag_slugs).distinct()
