from django.db import transaction
from rest_framework_json_api import serializers

from apps.accounts.models import Profile, SocialMediaProfile


class SocialMediaProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = SocialMediaProfile
        fields = ("id", "platform", "url", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    class JSONAPIMeta:
        resource_name = "social-media-profiles"

    def validate(self, attrs):
        platform = attrs.get("platform")
        url = attrs.get("url")

        if platform and url:
            platform_domains = {
                "facebook": ["facebook.com"],
                "github": ["github.com"],
                "instagram": ["instagram.com"],
                "linkedin": ["linkedin.com"],
                "tiktok": ["tiktok.com"],
                "twitter": ["twitter.com"],
                "x": ["x.com"],
                "youtube": ["youtube.com"],
            }

            expected = platform_domains.get(platform)
            if expected and not any(d in url for d in expected):
                raise serializers.ValidationError(
                    {"url": [f"The URL must be a valid {platform} link."]}
                )

        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    social_media = SocialMediaProfileSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "biography",
            "location",
            "occupation",
            "skills",
            "experience_years",
            "social_media",
        )

    class JSONAPIMeta:
        resource_name = "profiles"
        included_resources = ["social_media"]


class PublicProfileSerializer(ProfileSerializer):
    pass


class PrivateProfileSerializer(ProfileSerializer):
    social_media = SocialMediaProfileSerializer(many=True, required=False)

    class Meta(ProfileSerializer.Meta):
        model = Profile
        fields = (
            *ProfileSerializer.Meta.fields,
            "is_public",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    class JSONAPIMeta:
        resource_name = "profiles"
        included_resources = ["social_media"]

    def create(self, validated_data):
        social_data = validated_data.pop("social_media", None)

        with transaction.atomic():
            instance = Profile.objects.create(**validated_data)
            self._put_social_media(instance, social_data)
            return instance

    def update(self, instance, validated_data):
        social_media_data = validated_data.pop("social_media", None)

        with transaction.atomic():
            if self.partial:
                self._patch_instance(instance, validated_data)
                self._patch_social_media(instance, social_media_data)

            else:
                self._put_instance(instance, validated_data)
                self._put_social_media(instance, social_media_data)

        return instance

    def _patch_instance(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

    def _put_instance(self, instance, validated_data):
        fields = (
            "biography",
            "location",
            "occupation",
            "skills",
            "experience_years",
        )

        for field in fields:
            default_value = [] if field == "skills" else None
            value = validated_data.get(field, default_value)
            setattr(instance, field, value)

        instance.save()

    def _put_social_media(self, instance, social_data):
        instance.social_media.all().delete()

        if social_data:
            SocialMediaProfile.objects.bulk_create(
                objs=[
                    SocialMediaProfile(profile=instance, **item) for item in social_data
                ]
            )

    def _patch_social_media(self, instance, social_data):
        if social_data is None:
            return

        existing = {
            social_profile.id: social_profile
            for social_profile in instance.social_media.all().only(
                "id", "platform", "url"
            )
        }

        incoming_ids = set()
        to_create = []
        to_update = []

        for item in social_data:
            social_profile_id = item.get("id")

            if social_profile_id and social_profile_id in existing:
                obj = existing[social_profile_id]
                obj.platform = item.get("platform", obj.platform)
                obj.url = item.get("url", obj.url)
                to_update.append(obj)
                incoming_ids.add(social_profile_id)
            else:
                item.pop("id", None)
                to_create.append(SocialMediaProfile(profile=instance, **item))

        if to_create:
            SocialMediaProfile.objects.bulk_create(to_create)

        if to_update:
            SocialMediaProfile.objects.bulk_update(to_update, ["platform", "url"])

        to_delete_ids = set(existing.keys()) - incoming_ids

        if to_delete_ids:
            SocialMediaProfile.objects.filter(id__in=to_delete_ids).delete()


class ProfileVisibilitySerializer(serializers.Serializer):
    class Meta:
        model = Profile
        fields = ["is_public"]
