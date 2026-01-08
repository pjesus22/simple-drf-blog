from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EditorProfile, User


@receiver(signal=post_save, sender=User)
def create_editor_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.EDITOR:
        EditorProfile.objects.get_or_create(user=instance)
