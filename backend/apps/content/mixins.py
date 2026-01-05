from django.db.models import Q

from .models import Post


class PostFilterMixin:
    def get_filtered_posts_queryset(self):
        user = self.request.user

        if user.is_authenticated:
            if user.role == "admin":
                return Post.objects.all()

            if user.role == "editor":
                return Post.objects.filter(
                    Q(status=Post.Status.PUBLISHED) | Q(author=user)
                )

        return Post.objects.filter(status=Post.Status.PUBLISHED)
