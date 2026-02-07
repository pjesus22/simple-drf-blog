from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, User


@receiver(signal=post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.EDITOR:
        Profile.objects.get_or_create(user=instance)
