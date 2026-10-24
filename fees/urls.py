from django.urls import path

from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.manage, name='manage'),
    path('student/<int:student_id>/', views.student_fees, name='student_fees'),
    path('student/<int:student_id>/fees/new/', views.fee_create, name='fee_create'),
    path('fees/<int:fee_id>/edit/', views.fee_edit, name='fee_edit'),
    path('fees/<int:fee_id>/pay/', views.payment_create, name='payment_create'),
    path('payments/<int:payment_id>/receipt/', views.receipt, name='receipt'),
    path('my/', views.my_fees, name='my_fees'),
    path('dues/', views.dues_report, name='dues_report'),
]
