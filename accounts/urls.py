from django.urls import path

from . import user_views

app_name = 'accounts'

urlpatterns = [
    path('users/', user_views.user_list, name='users'),
    path('users/new/', user_views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', user_views.user_edit, name='user_edit'),
    path('users/<int:pk>/deactivate/', user_views.user_deactivate, name='user_deactivate'),
    path('users/<int:pk>/reactivate/', user_views.user_reactivate, name='user_reactivate'),
    path('users/<int:pk>/unlock/', user_views.user_unlock, name='user_unlock'),
]
