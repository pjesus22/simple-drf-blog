from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Editor, EditorProfile


@receiver(signal=post_save, sender=Editor)
def create_editor_profile(sender, instance, created, **kwargs):
    if created:
        EditorProfile.objects.get_or_create(user=instance)
