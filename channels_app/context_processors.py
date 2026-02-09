from .models import Notification

def notification_context(request):
    """
    This function name must match exactly what is in settings.py
    """
    if request.user.is_authenticated:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {
            'unread_count': count
        }
    return {
        'unread_count': 0
    }