from django.urls import path

from . import views

app_name = 'notices'

urlpatterns = [
    # Public / Student Notice Board
    path('board/', views.board, name='board'),

    # Staff Management (Warden / Admin)
    path('manage/', views.manage_notices, name='manage'),
    path('add/', views.notice_add, name='add'),
    path('<int:pk>/edit/', views.notice_edit, name='edit'),
    path('<int:pk>/delete/', views.notice_delete, name='delete'),
    path('<int:pk>/expire/', views.notice_expire, name='expire'),
]
