from django.contrib import admin
from django.urls import include, path
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # NFR-08: Health check endpoint
    path('health/', core_views.health_check, name='health_check'),
    # Login, logout and password reset (FR-01).
    path('', include('accounts.auth_urls')),
    path('accounts/', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('rooms/', include('rooms.urls')),
    path('allocation/', include('allocation.urls')),
    path('attendance/', include('attendance.urls')),
    path('complaints/', include('complaints.urls')),
    path('fees/', include('fees.urls')),
    path('visitors/', include('visitors.urls')),
    path('leave/', include('leave.urls')),
    path('notices/', include('notices.urls')),
    path('', include('core.urls')),
]

# NFR-04, NFR-09: Custom error handlers (graceful failure, no stack traces)
handler400 = 'core.views.bad_request_view'
handler403 = 'core.views.permission_denied_view'
handler404 = 'core.views.page_not_found_view'
handler500 = 'core.views.server_error_view'

