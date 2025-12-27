from apps.users.models import EditorProfile, SocialLink


def test_editor_profile_str_returns_username(db, editor_factory):
    user = editor_factory(profile=True)
    profile = EditorProfile.objects.get(user=user)
    assert str(profile) == f"EditorProfile (ID: {profile.id})"


def test_social_link_str_returns_name_and_url():
    social_link = SocialLink(name="GitHub", url="github-fake.com")
    assert str(social_link) == "GitHub - github-fake.com"
