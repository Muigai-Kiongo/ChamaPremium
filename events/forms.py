from django import forms
from .models import Event, EventImage
from django.utils.timezone import now

from django.utils.timezone import now

class EventForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    class Meta:
        model = Event
        fields = ["title", "description", "start_date", "end_date"]

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end:
            if start >= end:
                raise forms.ValidationError("Start date must be before end date.")
            if start < now():
                raise forms.ValidationError("Start date cannot be in the past.")
        return cleaned_data

class EventImageForm(forms.ModelForm):
    class Meta:
        model = EventImage
        fields = ["image"]

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            if image.size > 2 * 1024 * 1024:  # 2MB limit
                raise forms.ValidationError("Image file too large (max 2MB).")
            if not image.content_type in ["image/jpeg", "image/png"]:
                raise forms.ValidationError("Only JPEG and PNG images are allowed.")
        return image