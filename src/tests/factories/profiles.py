import factory
from faker import Faker

_fake = Faker()


class ProfileFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(
        factory="tests.factories.accounts.EditorFactory",
        profile=None,
    )
    biography = factory.Faker("text")
    location = factory.Faker("city")
    occupation = factory.Faker("job")
    skills = factory.Faker("sentence", nb_words=5)
    experience_years = factory.Faker("random_int", min=0, max=40)

    class Meta:
        model = "accounts.Profile"


class SocialMediaProfileFactory(factory.django.DjangoModelFactory):
    profile = factory.SubFactory(ProfileFactory)
    platform = factory.Faker(
        provider="random_element",
        elements=(
            "facebook",
            "github",
            "instagram",
            "linkedin",
            "tiktok",
            "twitter",
            "youtube",
        ),
    )

    class Meta:
        model = "accounts.SocialMediaProfile"

    @factory.lazy_attribute
    def url(self):
        return f"https://{self.platform}.com/{_fake.user_name()}"
