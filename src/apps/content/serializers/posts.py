from rest_framework_json_api import serializers

from apps.content.models import Category, Post, Tag
from apps.uploads.models import Upload


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ResourceRelatedField(read_only=True)
    category = serializers.ResourceRelatedField(
        queryset=Category.objects.all(),
    )
    tags = serializers.ResourceRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    thumbnail = serializers.ResourceRelatedField(
        queryset=Upload.objects.filter(purpose=Upload.Purpose.THUMBNAIL),
        allow_null=True,
    )
    attachments = serializers.ResourceRelatedField(
        many=True,
        queryset=Upload.objects.filter(purpose=Upload.Purpose.ATTACHMENT),
    )

    included_serializers = {
        "author": "apps.accounts.serializers.UserListSerializer",
        "category": "apps.content.serializers.CategorySerializer",
        "tags": "apps.content.serializers.TagSerializer",
        "thumbnail": "apps.uploads.serializers.UploadSerializer",
        "attachments": "apps.uploads.serializers.UploadSerializer",
    }

    class Meta:
        model = Post
        fields = (
            "id",
            "title",
            "slug",
            "content",
            "summary",
            "status",
            "published_at",
            "created_at",
            "updated_at",
            "author",
            "category",
            "tags",
            "thumbnail",
            "attachments",
        )
        resource_name = "posts"
        read_only_fields = ("id", "created_at", "updated_at", "published_at")


class PostCreateSerializer(PostSerializer):
    title = serializers.CharField(required=True)
    content = serializers.CharField(required=True)
    slug = serializers.CharField(required=False)
    category = serializers.ResourceRelatedField(
        queryset=Category.objects.all(),
        required=True,
    )
    tags = serializers.ResourceRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False,
    )
    thumbnail = serializers.ResourceRelatedField(
        queryset=Upload.objects.filter(purpose=Upload.Purpose.THUMBNAIL).all(),
        allow_null=True,
        required=False,
    )
    attachments = serializers.ResourceRelatedField(
        many=True,
        queryset=Upload.objects.filter(purpose=Upload.Purpose.ATTACHMENT).all(),
        required=False,
    )

    class Meta(PostSerializer.Meta):
        pass


class PostUpdateSerializer(serializers.ModelSerializer):
    category = serializers.ResourceRelatedField(
        queryset=Category.objects.all(), required=False
    )
    tags = serializers.ResourceRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )

    class Meta:
        model = Post
        fields = (
            "title",
            "slug",
            "content",
            "summary",
            "category",
            "tags",
        )


class PostStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Post.Status.choices, required=True)

    class Meta:
        model = Post
        fields = ("status",)

    def validate_status(self, value):
        post = self.instance

        if post.is_deleted:
            raise serializers.ValidationError(
                detail="Cannot change status of a deleted post.",
                code="not_deleted",
            )

        return value

    def save(self, **kwargs):
        post = self.instance
        new_status = self.validated_data["status"]
        post.change_status(new_status)
        return post


class PostThumbnailSerializer(serializers.Serializer):
    id = serializers.UUIDField()

    def validate_id(self, value):
        try:
            return Upload.objects.get(id=value, purpose=Upload.Purpose.THUMBNAIL)
        except Upload.DoesNotExist:
            raise serializers.ValidationError("Invalid thumbnail upload.") from None


class PostAttachmentAddSerializer(serializers.Serializer):
    attachments = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate_attachments(self, values):
        uploads = Upload.objects.filter(
            id__in=values, purpose=Upload.Purpose.ATTACHMENT
        )

        if uploads.count() != len(set(values)):
            raise serializers.ValidationError("One or more attachments are invalid.")

        return uploads


class PostAttachmentRemoveSerializer(serializers.Serializer):
    attachment_id = serializers.UUIDField()

    def validate_attachment_id(self, value):
        post = self.context["post"]
        try:
            return post.attachments.get(id=value, purpose=Upload.Purpose.ATTACHMENT)
        except Upload.DoesNotExist:
            raise serializers.ValidationError(
                "Attachment not found in this post"
            ) from None


class PostSoftDeleteSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(
        required=True,
        help_text="Must be true to confirm selection",
    )
    reason = serializers.CharField(
        required=False,
        max_length=200,
        allow_blank=True,
        help_text="Optional reason for deletion",
    )

    def validate(self, attrs):
        post = self.instance

        if post.is_deleted:
            raise serializers.ValidationError(
                detail="This post is already deleted.",
                code="already_deleted",
            )

        if not attrs.get("confirm", False):
            raise serializers.ValidationError(
                detail="Must confirm deletion by setting 'confirm=true'",
                code="confirmation_required",
            )

        return attrs

    def save(self):
        post = self.instance
        post.soft_delete()
        return post


class PostRestoreSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(
        required=True,
        help_text="Must be true to confirm restoration",
    )

    def validate(self, attrs):
        post = self.instance

        if not post.is_deleted:
            raise serializers.ValidationError(
                detail="Only deleted posts can be restored.",
                code="not_deleted",
            )

        if not attrs.get("confirm", False):
            raise serializers.ValidationError(
                detail="Must confirm restoration by setting 'confirm=true'",
                code="confirmation_required",
            )

        return attrs

    def save(self):
        post = self.instance
        post.restore()
        return post
