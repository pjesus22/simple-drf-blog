from apps.content.models import Post
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PostMetric


@receiver(signal=post_save, sender=Post)
def create_post_metric(sender, instance, created, **kwargs):
    if created:
        PostMetric.objects.get_or_create(post=instance)
