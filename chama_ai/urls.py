from django.urls import path
from . import views

app_name = 'chama_ai'

urlpatterns = [
    path('live/', views.live_meeting, name='live_meeting'),
    path('notes/<int:meeting_id>/', views.ai_notes, name='ai_notes'),
    path('ws/meeting/<int:meeting_id>/', ...),
]
