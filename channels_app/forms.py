from django import forms
from django.utils import timezone
from .models import Request, Webinar

class WebinarForm(forms.ModelForm):
    class Meta:
        model = Webinar
        fields = ['title', 'description', 'scheduled_at', 'duration_minutes', 
                 'google_meet_link', 'status']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'google_meet_link': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = timezone.now()
        self.fields['scheduled_at'].min = now.strftime('%Y-%m-%dT%H:%M')

    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data['scheduled_at']
        if scheduled_at < timezone.now():
            raise forms.ValidationError("Cannot schedule past webinars")
        return scheduled_at
    
class RequestForm(forms.ModelForm):
    class Meta:
            model = Request
            fields = ['type', 'title', 'description', 'amount']
            widgets = {
                'type': forms.Select(attrs={'class': 'form-select'}),
                'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Brief title for your request'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Explain your request in detail...'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Amount in KSh',
                'min': '0',
                'step': '1'
            }),
        }
            labels = {
            'type': 'Request Type',
            'title': 'Request Title',
            'description': 'Detailed Description',
            'amount': 'Amount (KSh)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        req_type = cleaned_data.get('type')
        amount = cleaned_data.get('amount')
        
        if req_type == 'financial' and not amount:
            raise forms.ValidationError("Amount is required for financial requests")
        
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero")
        
        return cleaned_data

