from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/student/', views.dashboard_student, name='dashboard_student'),
    path('dashboard/warden/', views.dashboard_warden, name='dashboard_warden'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
]
