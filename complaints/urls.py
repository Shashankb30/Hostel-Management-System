from django.urls import path

from . import views

app_name = 'complaints'

urlpatterns = [
    # Student
    path('', views.my_complaints, name='my_complaints'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/edit/', views.edit, name='edit'),
    # Warden and administrator
    path('manage/', views.manage, name='manage'),
    path('manage/misconduct/', views.log_misconduct, name='log_misconduct'),
    path('manage/rules/', views.rules, name='rules'),
    path('manage/report/', views.report, name='report'),
    path('manage/<int:pk>/status/', views.update_status, name='update_status'),
    path('manage/<int:pk>/reopen/', views.reopen, name='reopen'),
    path('manage/<int:pk>/escalate/', views.escalate, name='escalate'),
]
