from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.text import slugify

from .forms import WebinarForm, RequestForm
from .models import (
    Channel, ChannelMembership, Webinar, WebinarAttendance, 
    Request, Notification
)

# === AUTHENTICATION ===

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect(request.GET.get('next', 'channels_app:channel_list'))
    else:
        form = AuthenticationForm()
    return render(request, 'channels_app/login.html', {'form': form})

@require_POST
def user_logout(request):
    logout(request)
    return redirect('login')

# === CHANNELS ===

def is_channel_moderator(user):
    return user.is_authenticated and user.groups.filter(name__in=['Chama Admins', 'Moderators']).exists()

@login_required
def channel_list(request):
    channels = Channel.objects.filter(is_private=False).order_by('-created_at')
    return render(request, 'channels_app/channel_list.html', {'channels': channels})

@login_required
@user_passes_test(is_channel_moderator, login_url='login')
def channel_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        channel = Channel.objects.create(
            name=name,
            slug=slugify(name),
            description=request.POST.get('description', ''),
            creator=request.user
        )
        ChannelMembership.objects.create(user=request.user, channel=channel, role='admin')
        messages.success(request, f'Channel "{name}" created!')
        return redirect('channels_app:channel_list')
    return render(request, 'channels_app/channel_create.html')

@login_required
def channel_detail(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    membership = ChannelMembership.objects.filter(channel=channel, user=request.user, is_active=True).first()
    
    if not membership:
        return render(request, 'channels_app/channel_join.html', {'channel': channel})
    
    context = {
        'channel': channel,
        'membership': membership,
        'is_admin': membership.role == 'admin',
        'recent_webinars': channel.webinars.all()[:3],
    }
    return render(request, 'channels_app/channel_detail.html', context)

# === WEBINARS ===

@login_required
def webinar_create(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    membership = ChannelMembership.objects.filter(channel=channel, user=request.user, role='admin', is_active=True).first()
    
    if not membership:
        messages.error(request, "Only admins can create webinars")
        return redirect('channels_app:channel_detail', slug=channel_slug)
    
    if request.method == 'POST':
        form = WebinarForm(request.POST)
        if form.is_valid():
            webinar = form.save(commit=False)
            webinar.channel = channel
            webinar.created_by = request.user
            webinar.save()
            
            # Notify members
            members = ChannelMembership.objects.filter(channel=channel, is_active=True).exclude(user=request.user)
            notifications = [
                Notification(
                    recipient=m.user,
                    title='New Webinar Scheduled',
                    message=f'"{webinar.title}" in {channel.name}',
                    notification_type='webinar',
                    link=f'/channel/{channel.slug}/webinars/{webinar.id}/'
                ) for m in members
            ]
            Notification.objects.bulk_create(notifications)
            
            messages.success(request, 'Webinar created!')
            return redirect('channels_app:webinar_list', channel_slug=channel.slug)
    else:
        form = WebinarForm()
    return render(request, 'channels_app/webinar_form.html', {'form': form, 'channel': channel})

@login_required
def webinar_list(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    webinars = Webinar.objects.filter(channel=channel).order_by('-scheduled_at')
    return render(request, 'channels_app/webinar_list.html', {'channel': channel, 'webinars': webinars})

@login_required
def webinar_detail(request, channel_slug, webinar_id):
    webinar = get_object_or_404(Webinar, id=webinar_id, channel__slug=channel_slug)
    return render(request, 'channels_app/webinar_detail.html', {'webinar': webinar})

@login_required
def webinar_join(request, channel_slug, webinar_id):
    webinar = get_object_or_404(Webinar, id=webinar_id, channel__slug=channel_slug)
    membership = ChannelMembership.objects.get(channel=webinar.channel, user=request.user, is_active=True)
    WebinarAttendance.objects.get_or_create(webinar=webinar, member=membership)
    return JsonResponse({'success': True, 'meet_link': webinar.google_meet_link})

# === NOTIFICATIONS ===

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'channels_app/notifications.html', {'notifications': notifications})

@login_required
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('channels_app:notifications_list')

@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect('channels_app:notifications_list')

@login_required
def notification_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})

def delete_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    return redirect('channels_app:notifications_list')

# === REQUESTS ===

@login_required
def request_list(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    reqs = Request.objects.filter(channel=channel).order_by('-created_at')
    return render(request, 'channels_app/request_list.html', {'channel': channel, 'requests': reqs})

@login_required
def request_create(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            new_req = form.save(commit=False)
            new_req.channel = channel
            new_req.requester = request.user
            new_req.save()
            return redirect('channels_app:request_list', channel_slug=channel_slug)
    else:
        form = RequestForm()
    return render(request, 'channels_app/request_form.html', {'form': form, 'channel': channel})

@login_required
def request_detail(request, channel_slug, request_id):
    channel = get_object_or_404(Channel, slug=channel_slug)
    req = get_object_or_404(Request, id=request_id, channel=channel)
    return render(request, 'channels_app/request_detail.html', {'channel': channel, 'request': req})

@login_required
def request_approve(request, channel_slug, request_id):
    """FIX: Added missing request_approve view"""
    req = get_object_or_404(Request, id=request_id, channel__slug=channel_slug)
    # Check if user is admin of the channel
    membership = get_object_or_404(ChannelMembership, channel=req.channel, user=request.user, role='admin')
    
    req.status = 'approved'
    req.save()
    
    # Notify the requester
    Notification.objects.create(
        recipient=req.requester,
        title="Request Approved ",
        message=f"Your request in {req.channel.name} has been approved.",
        notification_type="request_status"
    )
    
    messages.success(request, "Request approved.")
    return redirect('channels_app:request_list', channel_slug=channel_slug)

@login_required
def request_reject(request, channel_slug, request_id):
    """FIX: Added missing request_reject view (usually paired with approve)"""
    req = get_object_or_404(Request, id=request_id, channel__slug=channel_slug)
    membership = get_object_or_404(ChannelMembership, channel=req.channel, user=request.user, role='admin')
    
    req.status = 'rejected'
    req.save()
    
    messages.warning(request, "Request rejected.")
    return redirect('channels_app:request_list', channel_slug=channel_slug)