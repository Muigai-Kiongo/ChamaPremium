from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from .models import Event, EventImage
from .forms import EventForm, EventImageForm

# Utility function to check if user is admin
def is_admin(user):
    return user.is_staff  # assuming admin users have is_staff=True

# List of events - everyone can view
@login_required
def event_list(request):
    events = Event.objects.all().order_by('-start_date')
    paginator = Paginator(events, 8)  # show 8 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'events/event_list.html', {'events': page_obj})

# Event detail view - everyone can view
@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    images = event.images.all()
    return render(request, 'events/event_detail.html', {'event': event, 'images': images})

# Create event - admin only
@login_required
@user_passes_test(is_admin)
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = EventForm()
    return render(request, 'events/event_form.html', {'form': form, 'action': 'Create'})

# Update event - admin only
@login_required
@user_passes_test(is_admin)
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    return render(request, 'events/event_form.html', {'form': form, 'action': 'Update'})

# Delete event - admin only
@login_required
@user_passes_test(is_admin)
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        return redirect('events:event_list')
    return render(request, 'events/event_confirm_delete.html', {'event': event})

# Optional: add event images - admin only
@login_required
@user_passes_test(is_admin)
def add_event_image(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.event = event
            image.save()
            return redirect('events:event_detail', pk=event.pk)
    else:
        form = EventImageForm()
    return render(request, 'events/add_event_image.html', {'form': form, 'event': event})

