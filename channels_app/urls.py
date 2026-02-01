from django.urls import path
from . import views

app_name = 'channels_app'

urlpatterns = [
    # Auth
    path('login/', views.user_login, name='login'),
    
    # Channels
    path('', views.channel_list, name='channel_list'),
    path('channel/<slug:slug>/', views.channel_detail, name='channel_detail'),
    
    # Webinars
    path('channel/<slug:channel_slug>/webinars/', views.webinar_list, name='webinar_list'),
    path('channel/<slug:channel_slug>/webinars/create/', views.webinar_create, name='webinar_create'),
    path('channel/<slug:channel_slug>/webinars/<int:webinar_id>/', views.webinar_detail, name='webinar_detail'),
    path('channel/<slug:channel_slug>/webinars/<int:webinar_id>/join/', views.webinar_join, name='webinar_join'),
    
    # Requests
    path('channel/<slug:channel_slug>/requests/', views.request_list, name='request_list'),
    path('channel/<slug:channel_slug>/requests/create/', views.request_create, name='request_create'),
    path('channel/<slug:channel_slug>/requests/<int:request_id>/', views.request_detail, name='request_detail'),
    path('channel/<slug:channel_slug>/requests/<int:request_id>/approve/', views.request_approve, name='request_approve'),
    path('channel/<slug:channel_slug>/requests/<int:request_id>/reject/', views.request_reject, name='request_reject'),


    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('api/notifications/count/', views.notification_count, name='notification_count'),
]