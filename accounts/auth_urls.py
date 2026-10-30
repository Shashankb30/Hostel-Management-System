"""Login, logout and password reset routes. Names are global (no namespace) because
settings.LOGIN_URL, the base template and Django's own views refer to them directly."""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.HmsLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.HmsPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.HmsPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
]
