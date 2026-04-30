from django.db import IntegrityError, models, transaction
from django.utils.text import slugify


class SlugMixin(models.Model):
    slug_field = "slug"
    slug_source_field = "title"
    slug_max_retries = 5

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        for _ in range(self.slug_max_retries):
            try:
                with transaction.atomic():
                    self._set_slug()
                    return super().save(*args, **kwargs)
            except IntegrityError:
                setattr(self, self.slug_field, None)

        raise IntegrityError("Could not generate a unique slug after retries")

    def _get_slug_field(self):
        return self.slug_field

    def _get_slug_source_value(self):
        return getattr(self, self.slug_source_field)

    def _slug_exists(self, slug):
        ModelClass = self.__class__
        slug_field = self._get_slug_field()

        qs = ModelClass.objects.filter(**{slug_field: slug})

        if self.pk:
            qs = qs.exclude(pk=self.pk)

        return qs.exists()

    def _generate_base_slug(self):
        return slugify(self._get_slug_source_value())

    def _generate_unique_slug(self):
        base_slug = self._generate_base_slug()
        slug = base_slug
        counter = 1

        while self._slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def _set_slug(self):
        slug_field = self._get_slug_field()
        current_slug = getattr(self, slug_field)

        if current_slug:
            setattr(self, slug_field, slugify(current_slug))
        else:
            setattr(self, slug_field, self._generate_unique_slug())
