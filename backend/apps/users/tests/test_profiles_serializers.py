from apps.users.serializers import EditorProfileSerializer, SocialLinkSerializer
from rest_framework.fields import DateTimeField

field = DateTimeField()


def test_editor_profiles_serializes_object(db, profile_factory):
    profile = profile_factory()
    serializer = EditorProfileSerializer(profile)
    expected = {
        "id": profile.id,
        "biography": profile.biography,
        "location": profile.location,
        "occupation": profile.occupation,
        "skills": profile.skills,
        "experience_years": profile.experience_years,
        "updated_at": field.to_representation(profile.updated_at),
        "social_links": [],
    }

    assert serializer.data == expected


def test_social_link_serializes_object(db, social_link_factory):
    socials = social_link_factory()
    expected = {
        "id": socials.id,
        "name": socials.name,
        "url": socials.url,
        "created_at": field.to_representation(socials.created_at),
        "updated_at": field.to_representation(socials.updated_at),
    }
    serializer = SocialLinkSerializer(socials)

    assert serializer.data == expected
