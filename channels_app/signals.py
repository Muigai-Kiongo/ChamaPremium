from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Webinar, Notification, ChannelMembership

@receiver(post_save, sender=Webinar)
def notify_members_of_webinar(sender, instance, created, **kwargs):
    if created:
        memberships = ChannelMembership.objects.filter(
            channel=instance.channel, 
            is_active=True
        ).exclude(user=instance.created_by)
        
        notifications = [
            Notification(
                recipient=m.user,
                channel=instance.channel,
                title="New Webinar Scheduled ",
                message=f"'{instance.title}' has been added to {instance.channel.name}.",
                type="webinar",
                is_read=False
            ) for m in memberships
        ]
        Notification.objects.bulk_create(notifications)