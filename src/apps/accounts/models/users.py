from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator
from django.db import models

from apps.accounts.managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"

    objects = UserManager()
    role = models.CharField(
        choices=Role.choices,
        max_length=16,
        default=Role.EDITOR,
    )
    username = models.CharField(
        max_length=32,
        unique=True,
        blank=False,
        null=False,
        validators=[MinLengthValidator(3, "Username must be at least 3 characters")],
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
    )
    first_name = models.CharField(
        max_length=64,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        max_length=64,
        blank=False,
        null=False,
    )

    def __str__(self):
        return self.get_full_name()

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    class Meta:
        ordering = ["-id"]


class AdminManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.ADMIN)


class Admin(User):
    objects = AdminManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.role = User.Role.ADMIN

        super().save(*args, **kwargs)


class EditorManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.EDITOR)


class Editor(User):
    objects = EditorManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.role = User.Role.EDITOR
        super().save(*args, **kwargs)
