from rest_framework_json_api import serializers

from ..models import EditorProfile, SocialLink


class SocialLinkSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = SocialLink
        fields = ("id", "name", "url", "created_at", "updated_at")
        resource_name = "social_links"
        read_only_fields = ("created_at", "updated_at")


class EditorProfileSerializer(serializers.ModelSerializer):
    social_links = SocialLinkSerializer(many=True)

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
        resource_name = "profiles"
        read_only_fields = ("id", "updated_at")

    def create(self, validated_data):
        social_links_data = validated_data.pop("social_links", [])
        instance = EditorProfile.objects.create(**validated_data)

        for link_data in social_links_data:
            SocialLink.objects.create(profile=instance, **link_data)

        return instance

    def update(self, instance, validated_data):
        social_links_data = validated_data.pop("social_links", None)

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update social links
        if social_links_data is not None:
            existing_links = {link.id: link for link in instance.social_links.all()}
            posted_links_ids = []

            for link_data in social_links_data:
                link_id = link_data.get("id")

                if link_id and link_id in existing_links:
                    link_instance = existing_links[link_id]
                    link_instance.name = link_data.get("name", link_instance.name)
                    link_instance.url = link_data.get("url", link_instance.url)
                    link_instance.save()
                    posted_links_ids.append(link_id)
                else:
                    link_data.pop("id", None)
                    new_link = SocialLink.objects.create(profile=instance, **link_data)
                    posted_links_ids.append(new_link.id)

            for link_id, link_instance in existing_links.items():
                if link_id not in posted_links_ids:
                    link_instance.delete()

        return instance
