from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Resume


@receiver(post_delete, sender=Resume)
def delete_file_with_resume(sender, instance, **kwargs):
    """Never leave uploaded files behind (covers resume delete AND account delete cascade)."""
    if instance.file:
        instance.file.delete(save=False)
