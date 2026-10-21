"""Login, logout and password reset routes. Names are global (no namespace) because
settings.LOGIN_URL, the base template and Django's own views refer to them directly."""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.HmsLoginView.as_view(), name='login'),
]
