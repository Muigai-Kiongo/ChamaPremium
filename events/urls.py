from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("create/", views.event_create, name="event_create"),
    path("<int:pk>/", views.event_detail, name="event_detail"),
    path("<int:pk>/upload/", views.upload_event_image, name="upload_event_image"),
    path("<int:pk>/delete/", views.event_delete, name="event_delete"),
    path("images/<int:pk>/delete/", views.event_image_delete, name="event_image_delete"),

]
