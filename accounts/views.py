"""Login, logout and password reset views (FR-01)."""
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import reverse

from core.roles import DASHBOARD_URL_NAMES, get_role

from .forms import LoginForm


class HmsLoginView(LoginView):
    """The one login page (FR-01.01). Anyone already logged in is sent on to their dashboard."""

    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    form_class = LoginForm

    def get_default_redirect_url(self):
        """After login, each role lands on its own dashboard (FR-01.02, FR-01.04)."""
        role = get_role(self.request.user)
        if role in DASHBOARD_URL_NAMES:
            return reverse(DASHBOARD_URL_NAMES[role])
        return resolve_url(settings.LOGIN_REDIRECT_URL)
