from apps.accounts.models import Profile, SocialMediaProfile
from django.db import transaction
from rest_framework_json_api import serializers


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
        fields = ProfileSerializer.Meta.fields + (
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

            if social_data:
                social_media_objects = [
                    SocialMediaProfile(profile=instance, **item) for item in social_data
                ]
                SocialMediaProfile.objects.bulk_create(social_media_objects)

            return instance

    def update(self, instance, validated_data):
        social_data = validated_data.pop("social_media", None)

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if social_data is not None:
                existing = {
                    s.id: s
                    for s in instance.social_media.all().only("id", "platform", "url")
                }

                incoming_ids = set()

                to_create = []
                to_update = []

                for item in social_data:
                    sid = item.get("id")
                    if sid and sid in existing:
                        obj = existing[sid]
                        obj.platform = item.get("platform", obj.platform)
                        obj.url = item.get("url", obj.url)
                        to_update.append(obj)
                        incoming_ids.add(sid)
                    else:
                        item.pop("id", None)
                        to_create.append(SocialMediaProfile(profile=instance, **item))

                if to_create:
                    SocialMediaProfile.objects.bulk_create(to_create)

                if to_update:
                    SocialMediaProfile.objects.bulk_update(
                        to_update, ["platform", "url"]
                    )

                for sid, obj in existing.items():
                    if sid not in incoming_ids:
                        obj.delete()

            return instance
