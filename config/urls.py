from django.contrib import admin
from django.urls import path, include
from lending import views as lending_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lending_views.check_eligibility_view, name='check_eligibility'),
    path('lending/', include('lending.urls')),
    path('wallet/', include('wallet.urls')),

    # Add auth URLs so /accounts/login/ works
    path('accounts/', include('django.contrib.auth.urls')),
]
