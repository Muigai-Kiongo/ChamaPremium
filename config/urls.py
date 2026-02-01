from django.contrib import admin
from django.urls import path, include
from lending import views as lending_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('channels_app.urls')),
    path('lending/', include('lending.urls')),
    path('wallet/', include('wallet.urls')),
    # Add auth URLs so /accounts/login/ works
    path('accounts/', include('django.contrib.auth.urls')),

]
