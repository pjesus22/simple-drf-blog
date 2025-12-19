from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinLengthValidator
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"

    base_role = Role.ADMIN
    role = models.CharField(
        choices=Role.choices,
        max_length=10,
        default=base_role,
    )
    username = models.CharField(
        max_length=30,
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
        max_length=50,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        max_length=50,
        blank=False,
        null=False,
    )

    def __str__(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.role = self.base_role
            self.is_staff = self.base_role == self.Role.ADMIN
            self.is_superuser = self.base_role == self.Role.ADMIN
        super().save(*args, **kwargs)

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
        self.is_staff = True
        self.is_superuser = True
        super().save(*args, **kwargs)


class EditorManager(BaseUserManager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.EDITOR)


class Editor(User):
    base_role = User.Role.EDITOR
    objects = EditorManager()

    class Meta:
        proxy = True
