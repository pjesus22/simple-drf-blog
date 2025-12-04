import factory


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
        skip_postgeneration_save = True

    username = factory.Faker("user_name")
    password = factory.PostGenerationMethodCall("set_password", "defaultpassword")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")


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
