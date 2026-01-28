from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.timezone import now

from .models import Event, EventImage
from .forms import EventForm, EventImageForm


def event_list(request):
    upcoming_events = Event.objects.filter(start_date__gte=now()).order_by("start_date")
    past_events = Event.objects.filter(end_date__lt=now()).order_by("-end_date")

    return render(
        request,
        "events/event_list.html",
        {
            "upcoming_events": upcoming_events,
            "past_events": past_events,
        },
    )


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    images = event.images.all()

    image_form = EventImageForm()

    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
            "images": images,
            "image_form": image_form,
        },
    )


def is_event_creator(user):
    # Adjust this logic to your project roles
    return user.is_staff or user.groups.filter(name__in=['group_leader', 'admin']).exists()


@login_required
@user_passes_test(is_event_creator)
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        files = request.FILES.getlist("images")  # handle multiple files
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            # Save uploaded images with uploaded_by
            for f in files:
                EventImage.objects.create(
                    event=event,
                    image=f,
                    uploaded_by=request.user  # <-- fixed
                )
            return redirect("events:event_list")
        print("Form errors:", form.errors)
    else:
        form = EventForm()
    return render(request, "events/event_form.html", {"form": form})

def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        event.delete()
        return redirect("events:event_list")
    return render(request, "events/event_confirm_delete.html", {"event": event})


@login_required
def upload_event_image(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        form = EventImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.event = event
            image.uploaded_by = request.user
            image.save()

    return redirect("events:event_detail", pk=pk)


@login_required
@user_passes_test(lambda u: u.is_staff)  # only admins
def event_image_delete(request, pk):
    image = get_object_or_404(EventImage, pk=pk)
    event_pk = image.event.pk
    if request.method == "POST":
        image.delete()
    return redirect("events:event_detail", pk=event_pk)