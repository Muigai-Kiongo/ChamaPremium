from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('join-chama/<int:chama_id>/', views.join_chama, name='join_chama'),
     path('', views.index_view, name='index'),
    path('profile-details', views.profile_detail_view, name='profile-details'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile-update/', views.profile_update_view, name='profile_update'), 
]
