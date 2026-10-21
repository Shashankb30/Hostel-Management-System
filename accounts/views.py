"""Login, logout and password reset views (FR-01)."""
from django.contrib.auth.views import LoginView


class HmsLoginView(LoginView):
    """The one login page (FR-01.01). Anyone already logged in is sent on to their dashboard."""

    template_name = 'registration/login.html'
    redirect_authenticated_user = True
