from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Login, logout and password reset (FR-01).
    path('', include('accounts.auth_urls')),
    path('accounts/', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('rooms/', include('rooms.urls')),
    path('allocation/', include('allocation.urls')),
    path('complaints/', include('complaints.urls')),
    path('fees/', include('fees.urls')),
    path('', include('core.urls')),
]
