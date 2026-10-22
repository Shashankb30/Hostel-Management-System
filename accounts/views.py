"""Login, logout and password reset views (FR-01)."""
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.shortcuts import resolve_url
from django.urls import reverse

from core.roles import DASHBOARD_URL_NAMES, get_role

from .forms import LoginForm
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.urls import reverse_lazy

from . import lockout
from .forms import StyledPasswordResetForm, StyledSetPasswordForm
from .services import hms_account


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


@require_POST
def logout_view(request):
    """End the session (FR-01.08). POST only, so a stray link cannot log anyone out."""
    was_logged_in = request.user.is_authenticated
    logout(request)
    if was_logged_in:
        messages.success(request, 'You have been logged out')
    return redirect(settings.LOGOUT_REDIRECT_URL)


class HmsPasswordResetView(PasswordResetView):
    """Step 1: ask for the account's email address and send a reset link (FR-01.09)."""

    form_class = StyledPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class HmsPasswordResetConfirmView(PasswordResetConfirmView):
    """Step 3: choose the new password. A good reset also clears the failed-login count."""

    form_class = StyledSetPasswordForm
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        account = hms_account(self.user)
        if account is not None:
            lockout.register_success(account)
        return response
