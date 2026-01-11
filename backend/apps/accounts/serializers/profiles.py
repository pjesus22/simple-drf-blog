from rest_framework_json_api import serializers

from ..models import EditorProfile, SocialLink


class SocialLinkSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = SocialLink
        fields = ("id", "name", "url", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")

    class JSONAPIMeta:
        resource_name = "social-links"

    def validate(self, data):
        name = data.get("name")
        url = data.get("url")

        if name and url:
            domain_map = {
                "facebook": ["facebook.com"],
                "github": ["github.com"],
                "instagram": ["instagram.com"],
                "linkedin": ["linkedin.com"],
                "tiktok": ["tiktok.com"],
                "twitter": ["twitter.com"],
                "x": ["x.com"],
                "youtube": ["youtube.com"],
            }
            expected_domains = domain_map.get(name.lower())
            if expected_domains:
                if not any(domain in url for domain in expected_domains):
                    raise serializers.ValidationError(
                        {"url": [f"The URL must be a valid {name} link."]}
                    )

        return data


class EditorProfileSerializer(serializers.ModelSerializer):
    social_links = SocialLinkSerializer(many=True, required=False)

    class Meta:
        model = EditorProfile
        fields = (
            "id",
            "biography",
            "location",
            "occupation",
            "skills",
            "experience_years",
            "updated_at",
            "social_links",
        )
        read_only_fields = ("id", "updated_at")

    class JSONAPIMeta:
        resource_name = "profiles"
        included_resources = ["social_links"]

    def create(self, validated_data):
        social_links_data = validated_data.pop("social_links", [])
        profile = EditorProfile.objects.create(**validated_data)

        SocialLink.objects.bulk_create(
            [
                SocialLink(profile=profile, **link_data)
                for link_data in social_links_data
            ]
        )

        return profile

    def update(self, instance, validated_data):
        social_links_data = validated_data.pop("social_links", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if social_links_data is not None:
            existing_links = {link.id: link for link in instance.social_links.all()}
            incoming_ids = set()

            to_create = []
            to_update = []

            for link_data in social_links_data:
                link_id = link_data.get("id")

                if link_id and link_id in existing_links:
                    link = existing_links[link_id]
                    link.name = link_data.get("name", link.name)
                    link.url = link_data.get("url", link.url)
                    to_update.append(link)
                    incoming_ids.add(link_id)
                else:
                    link_data.pop("id", None)
                    to_create.append(SocialLink(profile=instance, **link_data))

            if to_create:
                SocialLink.objects.bulk_create(to_create)

            if to_update:
                SocialLink.objects.bulk_update(to_update, ["name", "url"])

            # delete removed links
            for link_id, link in existing_links.items():
                if link_id not in incoming_ids:
                    link.delete()

        return instance
