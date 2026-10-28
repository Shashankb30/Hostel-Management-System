from django.urls import path

from . import views

app_name = 'attendance'

urlpatterns = [
    # Student
    path('', views.my_attendance, name='my_attendance'),
    # Warden and administrator
    path('manage/', views.manage, name='manage'),
    path('manage/check-in/', views.check_in, name='check_in'),
    path('manage/check-out/', views.check_out, name='check_out'),
    path('manage/bulk/', views.bulk, name='bulk'),
    path('manage/report/', views.report, name='report'),
    path('manage/student/<int:pk>/', views.student_history, name='student_history'),
]
