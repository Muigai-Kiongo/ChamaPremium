from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('join-chama/<int:chama_id>/', views.join_chama, name='join_chama'),
]
