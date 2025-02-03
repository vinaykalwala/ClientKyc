import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger('django')

def get_instance_changes(old_instance, new_instance):
    changes = []
    for field in new_instance._meta.fields:
        field_name = field.name
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(new_instance, field_name, None)
        if old_value != new_value:
            changes.append(f"{field_name}: '{old_value}' → '{new_value}'")
    return ", ".join(changes)

@receiver(post_save)
def log_create_or_update(sender, instance, created, **kwargs):
    if sender.__name__ == 'Session':  # Skip session saves
        return

    user = getattr(instance, 'modified_by', 'Unknown User')
    if created:
        logger.info(f"[CREATE] {instance.__class__.__name__} (ID: {instance.pk}) created by {user}.")
    else:
        old_instance = sender.objects.get(pk=instance.pk)
        changes = get_instance_changes(old_instance, instance)
        logger.info(f"[UPDATE] {instance.__class__.__name__} (ID: {instance.pk}) updated by {user}. Changes: {changes}")

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender.__name__ == 'Session':  # Skip session deletes
        return

    user = getattr(instance, 'modified_by', 'Unknown User')
    logger.info(f"[DELETE] {instance.__class__.__name__} (ID: {instance.pk}) deleted by {user}. Data: {instance.__dict__}")
