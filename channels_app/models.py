from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# CHANNEL MODELS
class Channel(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_channels')

    class Meta:
        indexes = [models.Index(fields=['slug'])]
    def __str__(self):
        return self.name

class ChannelMembership(models.Model):
    ROLE_CHOICES = [('member', 'Member'), ('admin', 'Admin')]
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channel_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['channel', 'user']

# WEBINAR MODELS
class Webinar(models.Model):
    STATUS_CHOICES = [('scheduled', 'Scheduled'), ('live', 'Live'), ('completed', 'Completed'), ('cancelled', 'Cancelled')]
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='webinars')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    google_meet_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_webinars')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    max_attendees = models.PositiveIntegerField(default=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.channel.name}"
    
    class Meta:
        indexes = [models.Index(fields=['channel', 'scheduled_at'])]
        ordering = ['-scheduled_at']

    def __str__(self):
        return self.title

    def can_join(self, user):
        if self.status != 'live': return False, "Not live"
        membership = self.channel.memberships.filter(user=user, is_active=True).first()
        return bool(membership), "Must be member" if not membership else "OK"

    @property
    def attendee_count(self):
        return self.attendance.count()

class WebinarAttendance(models.Model):
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name='attendance')
    member = models.ForeignKey(ChannelMembership, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_present(self):
        return self.left_at is None

    class Meta:
        unique_together = ['webinar', 'member']


# NOTIFICATIONS
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# CHAT
class ChatRoom(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='chat_rooms')
    name = models.CharField(max_length=100, default='General')
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# REQUESTS
class Request(models.Model):
    TYPE_CHOICES = [
        ('membership', 'Join Chama'),
        ('financial', 'Financial Request'),
        ('operational', 'Operational'),
        ('communication', 'Communication'),
        ('webinar', 'Webinar Related'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests_made')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)  # KSh
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='requests_resolved')

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['channel', 'status', 'type'])]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.title} ({self.status})"

