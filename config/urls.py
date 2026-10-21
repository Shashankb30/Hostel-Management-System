from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Temporary logout until FR-01.08 (Issue #23) adds the real one.
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Login, logout and password reset (FR-01).
    path('', include('accounts.auth_urls')),
    path('', include('core.urls')),
]
