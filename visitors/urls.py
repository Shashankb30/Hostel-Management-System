from django.urls import path

from . import views

app_name = 'visitors'

urlpatterns = [
    path('', views.visitor_log, name='log'),
    path('add/', views.visitor_add, name='add'),
    path('<int:pk>/checkout/', views.visitor_checkout, name='checkout'),
    path('report/', views.visitor_report, name='report'),
    path('student/<int:student_id>/', views.student_visitor_history, name='student_history'),
]
