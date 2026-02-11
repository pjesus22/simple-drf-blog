from django.utils.text import slugify
import factory

from apps.content.models import Category, Post, Tag


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker("name")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    description = factory.Faker("text")


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Faker("name")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    title = factory.Faker("name")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    content = factory.Faker("text")
    summary = factory.Faker("text")
    author = factory.SubFactory("tests.factories.accounts.EditorFactory")
    category = factory.SubFactory("tests.factories.content.CategoryFactory")
