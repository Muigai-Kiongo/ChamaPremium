from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from .forms import WebinarForm, RequestForm
from .models import (
    Channel, ChannelMembership, Webinar, WebinarAttendance, 
    Request, Notification
)


# === HELPER FUNCTIONS ===
def create_notification(recipient, title, message, notification_type, link=None):
    """Create a notification for a user"""
    Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )


# === AUTH VIEWS ===
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid credentials')
    else:
        form = AuthenticationForm()
    
    return render(request, 'channels_app/login.html', {'form': form})


# === CHANNEL VIEWS ===
@login_required
def channel_list(request):
    channels = Channel.objects.filter(is_private=False).order_by('-created_at')
    context = {'channels': channels}
    return render(request, 'channels_app/channel_list.html', context)


@login_required
def channel_detail(request, slug):
    channel = get_object_or_404(Channel, slug=slug)
    membership = ChannelMembership.objects.filter(
        channel=channel, user=request.user, is_active=True
    ).first()
    
    if not membership:
        if request.method == 'POST':
            messages.success(request, 'Join request sent to admins!')
            return redirect('channels_app:channel_detail', slug=slug)
        return render(request, 'channels_app/channel_join.html', {
            'channel': channel
        })
    
    context = {
        'channel': channel,
        'membership': membership,
        'is_admin': membership.role == 'admin',
        'recent_webinars': channel.webinars.all()[:3],
    }
    return render(request, 'channels_app/channel_detail.html', context)


# === WEBINAR VIEWS ===
@login_required
def webinar_list(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    membership = ChannelMembership.objects.filter(
        channel=channel, user=request.user, is_active=True
    ).first()
    
    if not membership:
        messages.error(request, "Must be channel member")
        return redirect('channels_app:channel_detail', slug=channel_slug)
    
    is_admin = membership.role == 'admin'
    webinars = Webinar.objects.filter(channel=channel)
    
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        webinars = webinars.filter(status=status_filter)
    
    paginator = Paginator(webinars, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'channel': channel,
        'webinars': page_obj,
        'is_admin': is_admin,
        'status_filter': status_filter,
    }
    return render(request, 'channels_app/webinar_list.html', context)


@login_required
def webinar_create(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    membership = ChannelMembership.objects.filter(
        channel=channel, user=request.user, role='admin', is_active=True
    ).first()
    
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
            
            # Notify all channel members
            channel_members = ChannelMembership.objects.filter(
                channel=channel, is_active=True
            ).exclude(user=request.user)
            
            for member in channel_members:
                create_notification(
                    recipient=member.user,
                    title='New Webinar Scheduled 📅',
                    message=f'"{webinar.title}" scheduled for {webinar.scheduled_at.strftime("%b %d, %Y at %I:%M %p")}',
                    notification_type='webinar_created',
                    link=f'/channel/{channel.slug}/webinars/{webinar.id}/'
                )
            
            messages.success(request, 'Webinar created and members notified!')
            return redirect('channels_app:webinar_list', channel_slug=channel.slug)
    else:
        form = WebinarForm()
    
    return render(request, 'channels_app/webinar_form.html', {
        'form': form, 'channel': channel, 'action': 'Create'
    })


@login_required
def webinar_detail(request, channel_slug, webinar_id):
    webinar = get_object_or_404(Webinar.objects.select_related('channel'), 
                               id=webinar_id, channel__slug=channel_slug)
    membership = ChannelMembership.objects.filter(
        channel=webinar.channel, user=request.user, is_active=True
    ).first()
    
    if not membership:
        messages.error(request, "Must be channel member")
        return redirect('channels_app:channel_detail', slug=webinar.channel.slug)
    
    can_join, reason = webinar.can_join(request.user)
    
    context = {
        'webinar': webinar,
        'membership': membership,
        'can_join': can_join,
        'join_reason': reason,
        'current_attendees': webinar.attendance.filter(left_at__isnull=True).count(),
    }
    return render(request, 'channels_app/webinar_detail.html', context)


@login_required
def webinar_join(request, channel_slug, webinar_id):
    webinar = get_object_or_404(Webinar.objects.select_related('channel'), 
                               id=webinar_id, channel__slug=channel_slug)
    
    can_join, reason = webinar.can_join(request.user)
    if not can_join:
        return JsonResponse({'success': False, 'error': reason})
    
    membership = ChannelMembership.objects.get(
        channel=webinar.channel, user=request.user, is_active=True
    )
    
    attendance, created = WebinarAttendance.objects.get_or_create(
        webinar=webinar, member=membership,
        defaults={'joined_at': timezone.now()}
    )
    
    # Notify webinar creator
    if created:
        create_notification(
            recipient=webinar.created_by,
            title='Webinar Attendance',
            message=f'{request.user.username} joined "{webinar.title}"',
            notification_type='webinar_joined',
            link=f'/channel/{channel_slug}/webinars/{webinar_id}/'
        )
    
    return JsonResponse({
        'success': True,
        'meet_link': webinar.google_meet_link,
        'message': f'Joined! ({webinar.attendee_count} attendees)'
    })


# === REQUESTS VIEWS ===
@login_required
def request_list(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    membership = ChannelMembership.objects.filter(
        channel=channel, user=request.user, is_active=True
    ).first()
    
    if not membership:
        messages.error(request, "Must be a channel member")
        return redirect('channels_app:channel_detail', slug=channel_slug)
    
    is_admin = membership.role == 'admin'
    
    if is_admin:
        requests_list = channel.requests.all()
    else:
        requests_list = channel.requests.filter(requester=request.user)
    
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        requests_list = requests_list.filter(status=status_filter)
    
    type_filter = request.GET.get('type', 'all')
    if type_filter != 'all':
        requests_list = requests_list.filter(type=type_filter)
    
    paginator = Paginator(requests_list.order_by('-created_at'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'channel': channel,
        'requests': page_obj,
        'is_admin': is_admin,
        'status_filter': status_filter,
        'type_filter': type_filter,
    }
    return render(request, 'channels_app/request_list.html', context)


@login_required
def request_create(request, channel_slug):
    channel = get_object_or_404(Channel, slug=channel_slug)
    membership = ChannelMembership.objects.filter(
        channel=channel, user=request.user, is_active=True
    ).first()
    
    if not membership:
        messages.error(request, "Must be a channel member")
        return redirect('channels_app:channel_detail', slug=channel_slug)
    
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.channel = channel
            new_request.requester = request.user
            new_request.save()
            
            # Notify all channel admins
            admins = ChannelMembership.objects.filter(
                channel=channel, role='admin', is_active=True
            )
            
            for admin in admins:
                create_notification(
                    recipient=admin.user,
                    title='New Request Submitted 📝',
                    message=f'{request.user.username} submitted a {new_request.get_type_display()} request: "{new_request.title}"',
                    notification_type='request_created',
                    link=f'/channel/{channel_slug}/requests/{new_request.id}/'
                )
            
            messages.success(request, f'{new_request.get_type_display()} request submitted!')
            return redirect('channels_app:request_list', channel_slug=channel.slug)
    else:
        form = RequestForm()
    
    context = {
        'form': form,
        'channel': channel,
    }
    return render(request, 'channels_app/request_form.html', context)


@login_required
def request_detail(request, channel_slug, request_id):
    req_obj = get_object_or_404(Request, id=request_id, channel__slug=channel_slug)
    membership = ChannelMembership.objects.filter(
        channel=req_obj.channel, user=request.user, is_active=True
    ).first()
    
    if not membership:
        messages.error(request, "Access denied")
        return redirect('channels_app:channel_detail', slug=channel_slug)
    
    is_admin = membership.role == 'admin'
    is_owner = req_obj.requester == request.user
    
    if not (is_admin or is_owner):
        messages.error(request, "You can only view your own requests")
        return redirect('channels_app:request_list', channel_slug=channel_slug)
    
    context = {
        'request_obj': req_obj,
        'channel': req_obj.channel,
        'is_admin': is_admin,
        'is_owner': is_owner,
    }
    return render(request, 'channels_app/request_detail.html', context)


@login_required
def request_approve(request, channel_slug, request_id):
    req_obj = get_object_or_404(Request, id=request_id, channel__slug=channel_slug)
    membership = ChannelMembership.objects.filter(
        channel=req_obj.channel, user=request.user, role='admin', is_active=True
    ).first()
    
    if not membership:
        messages.error(request, "Admin access required")
        return redirect('channels_app:request_list', channel_slug=channel_slug)
    
    if req_obj.status == 'pending':
        req_obj.status = 'approved'
        req_obj.resolved_at = timezone.now()
        req_obj.resolved_by = request.user
        req_obj.save()
        

@login_required
def request_reject(request, channel_slug, request_id):
    req_obj = get_object_or_404(Request, id=request_id, channel__slug=channel_slug)
    membership = ChannelMembership.objects.filter(
        channel=req_obj.channel, user=request.user, role='admin', is_active=True
    ).first()
    
    if not membership:
        messages.error(request, "Admin access required")
        return redirect('channels_app:request_list', channel_slug=channel_slug)
    
    if req_obj.status == 'pending':
        req_obj.status = 'rejected'
        req_obj.resolved_at = timezone.now()
        req_obj.resolved_by = request.user
        req_obj.save()
        
        # Create notification for requester
    create_notification(
            recipient=req_obj.requester,
            title='Request Rejected',
            message=f'Your {req_obj.get_type_display()} request "{req_obj.title}" was not approved.',
            notification_type='request_rejected',
            link=f'/channel/{channel_slug}/requests/{request_id}/'
        )
        
    messages.info(request, 'Request rejected')
    
    return redirect('channels_app:request_detail', channel_slug=channel_slug, request_id=request_id)


# === NOTIFICATIONS VIEWS ===
@login_required
def notifications_list(request):
    """List all user notifications"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:50]
    
    unread = notifications.filter(is_read=False)
    
    context = {
        'notifications': notifications,
        'unread_count': unread.count(),
    }
    return render(request, 'channels_app/notifications_list.html', context)


@login_required
def notification_mark_read(request, notification_id):
    """Mark single notification as read"""
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read!')
    return redirect('channels_app:notifications_list')


@login_required
def notification_mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read!')
    return redirect('channels_app:notifications_list')


@login_required
def notification_count(request):
    """API: Get unread notification count"""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})
