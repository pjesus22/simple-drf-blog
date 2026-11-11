from rest_framework_json_api import serializers

from apps.content.models import Category, Post, Tag
from apps.uploads.models import Upload


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ResourceRelatedField(read_only=True)
    category = serializers.ResourceRelatedField(queryset=Category.objects.all())
    tags = serializers.ResourceRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    thumbnail = serializers.ResourceRelatedField(
        queryset=Upload.objects.filter(purpose=Upload.Purpose.THUMBNAIL),
        allow_null=True,
        required=False,
    )
    attachments = serializers.ResourceRelatedField(
        many=True,
        queryset=Upload.objects.filter(purpose=Upload.Purpose.ATTACHMENT),
        required=False,
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
        read_only_fields = ("id", "created_at", "updated_at", "published_at", "status")


class PostCreateSerializer(PostSerializer):
    status = serializers.ChoiceField(choices=Post.Status.choices, required=False)

    class Meta(PostSerializer.Meta):
        read_only_fields = (*PostSerializer.Meta.read_only_fields, "slug", "author")

    def validate(self, attrs):
        thumbnail = attrs.get("thumbnail")
        attachments = attrs.get("attachments") or []

        if not thumbnail and not attachments:
            return attrs

        user = self.context["request"].user

        if thumbnail:
            if not user.is_admin and thumbnail.uploaded_by_id != user.id:
                raise serializers.ValidationError(
                    {"thumbnail": ["Invalid thumbnail upload."]}
                )
            used = Post.all_objects.filter(thumbnail=thumbnail)
            if self.instance is not None:
                used = used.exclude(pk=self.instance.pk)
            if used.exists():
                raise serializers.ValidationError(
                    {"thumbnail": ["Thumbnail is already used by another post."]}
                )

        for attachment in attachments:
            if not user.is_admin and attachment.uploaded_by_id != user.id:
                raise serializers.ValidationError(
                    {"attachments": ["One or more attachments are invalid."]}
                )

        return attrs

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        validated_data["status"] = Post.Status.DRAFT

        return super().create(validated_data)


class PostUpdateSerializer(serializers.ModelSerializer):
    category = serializers.ResourceRelatedField(queryset=Category.objects.all())
    tags = serializers.ResourceRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )

    included_serializers = {
        "category": "apps.content.serializers.CategorySerializer",
        "tags": "apps.content.serializers.TagSerializer",
    }

    class Meta:
        model = Post
        fields = ("title", "slug", "content", "summary", "category", "tags")

    def validate(self, attrs):
        instance = self.instance

        if instance and instance.is_published:
            forbidden = ("title", "category", "tags", "slug")
            errors = {
                k: f"Cannot change {k} on a published post. "
                "Please archive the post first."
                for k in forbidden
                if k in attrs
            }
            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class PostStatusSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Post.Status.choices, required=True)

    class Meta:
        model = Post
        fields = ("status",)

    def validate(self, attrs):
        post = self.instance

        if post.is_deleted:
            raise serializers.ValidationError(
                detail="Cannot change status of a deleted post.",
                code="not_deleted",
            )

        if attrs["status"] == Post.Status.PUBLISHED and not post.content:
            raise serializers.ValidationError(
                detail="Cannot publish a post without content.",
                code="no_content",
            )

        return attrs

    def save(self, **kwargs):
        post = self.instance
        post.transition_to(self.validated_data["status"])
        return post


class PostThumbnailSerializer(serializers.Serializer):
    id = serializers.UUIDField()

    def validate_id(self, value):
        try:
            upload = Upload.objects.get(
                id=value,
                purpose=Upload.Purpose.THUMBNAIL,
                uploaded_by=self.context["request"].user,
            )
        except Upload.DoesNotExist:
            raise serializers.ValidationError("Invalid thumbnail upload.") from None
        post = self.context.get("post")
        used = Post.all_objects.filter(thumbnail=upload)
        if post is not None:
            used = used.exclude(pk=post.pk)
        if used.exists():
            raise serializers.ValidationError(
                "Thumbnail is already used by another post."
            )

        return upload


class PostAttachmentAddSerializer(serializers.Serializer):
    attachments = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
    )

    def validate_attachments(self, values):
        uploads = Upload.objects.filter(
            id__in=values,
            purpose=Upload.Purpose.ATTACHMENT,
            uploaded_by=self.context["request"].user,
        )

        if uploads.count() != len(values):
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
    confirm = serializers.BooleanField(required=True)

    def validate(self, attrs):
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
    confirm = serializers.BooleanField(required=True)

    def validate(self, attrs):
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
