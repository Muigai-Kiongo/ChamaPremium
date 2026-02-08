from django.contrib import admin
from django.urls import path, include
from lending import views as lending_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('lending/', include('lending.urls')),
    path('wallet/', include('wallet.urls')),
    path('', include('user.urls')),
    # Add auth URLs so /accounts/login/ works
    path('accounts/', include('django.contrib.auth.urls')),
    path('notifications/', include('channels_app.urls', namespace='channels_app')),
]
