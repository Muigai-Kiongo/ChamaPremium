from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class Meeting(models.Model):
    name = models.CharField(max_length=200)
    chama_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class LiveNote(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    speaker = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    note_type = models.CharField(max_length=20)  # contribution, decision, member, schedule
    timestamp = models.DateTimeField(auto_now_add=True)
    
class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, null=True)
    prompt = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
