from django.urls import path

from . import views

app_name = 'rooms'

urlpatterns = [
    path('', views.room_manage, name='manage'),
    path('new/', views.room_add, name='add'),
    path('<int:pk>/edit/', views.room_edit, name='edit'),
    path('<int:pk>/delete/', views.room_delete, name='delete'),
    path('<int:pk>/deactivate/', views.room_deactivate, name='deactivate'),
    path('<int:pk>/reactivate/', views.room_reactivate, name='reactivate'),
    path('vacancy/', views.room_vacancy, name='vacancy'),
]
