import factory
from apps.users.models import User
from faker import Faker

_fake = Faker()


class BaseUserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    password = factory.django.Password("defaultpassword")

    class Meta:
        abstract = True
        django_get_or_create = ("username",)
        skip_postgeneration_save = True


class DefaultUserFactory(BaseUserFactory):
    class Meta:
        model = "users.User"

    @factory.post_generation
    def finalize(self, create, extracted, **kwargs):
        if create:
            if self.role == User.Role.ADMIN:
                self.is_staff = True
                self.is_superuser = True
            else:
                self.is_staff = False
                self.is_superuser = False
            self.save(update_fields=["is_staff", "is_superuser"])


class AdminFactory(BaseUserFactory):
    role = User.Role.ADMIN

    class Meta:
        model = "users.Admin"

    @factory.post_generation
    def finalize(self, create, extracted, **kwargs):
        if create and self.role == User.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
            self.save(update_fields=["is_staff", "is_superuser"])


class EditorFactory(BaseUserFactory):
    role = User.Role.EDITOR

    class Meta:
        model = "users.Editor"

    @factory.post_generation
    def finalize(self, create, extracted, **kwargs):
        if create and self.role == User.Role.EDITOR:
            self.is_staff = False
            self.is_superuser = False
            self.save(update_fields=["is_staff", "is_superuser"])

    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted is True:
            ProfileFactory(user=self)


class ProfileFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(
        factory=EditorFactory,
        profile=None,
    )
    biography = factory.Faker("text")
    location = factory.Faker("city")
    occupation = factory.Faker("job")
    skills = factory.Faker("sentence", nb_words=5)
    experience_years = factory.Faker("random_int", min=0, max=40)

    class Meta:
        model = "users.EditorProfile"


class SocialLinkFactory(factory.django.DjangoModelFactory):
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

    class Meta:
        model = "users.SocialLink"

    @factory.lazy_attribute
    def url(self):
        return f"https://{self.name}.com/{_fake.user_name()}"
