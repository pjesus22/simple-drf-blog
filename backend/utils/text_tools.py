from django.utils.text import slugify


def generate_slug(instance, field_value: str, slug_field: str = "slug") -> str:
    ModelClass = instance.__class__
    base_slug = slugify(field_value)
    slug = base_slug
    n = 1

    while ModelClass.objects.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{n}"
        n += 1

    return slug
