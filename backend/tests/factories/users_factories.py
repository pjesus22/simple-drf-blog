import factory
from faker import Faker

fake = Faker()


class AdminFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.Admin"
        skip_postgeneration_save = True

    username = factory.Faker("user_name")
    password = factory.PostGenerationMethodCall("set_password", "defaultpassword")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")


class EditorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.Editor"
        django_get_or_create = ("username",)
        skip_postgeneration_save = True

    username = factory.Faker("user_name")
    password = factory.PostGenerationMethodCall("set_password", "defaultpassword")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")

    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is not None:
            if extracted is True:
                ProfileFactory(user=self)
            elif isinstance(extracted, dict):
                ProfileFactory(user=self, **extracted)
            else:
                self.profile = extracted
                self.save()


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.EditorProfile"
        skip_postgeneration_save = True

    user = factory.SubFactory(EditorFactory)
    biography = factory.Faker("text")
    location = factory.Faker("city")
    occupation = factory.Faker("job")
    skills = factory.Faker("sentence", nb_words=5)
    experience_years = factory.Faker("random_int", min=0, max=40)


class SocialLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "users.SocialLink"

    profile = factory.SubFactory(ProfileFactory)
    name = factory.Faker(
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

    @factory.lazy_attribute
    def url(self):
        return f"{self.name}/@{fake.user_name()}"
