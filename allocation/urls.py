from django.urls import path

from . import views

app_name = 'allocation'

urlpatterns = [
    path('', views.manage, name='manage'),
    path('allocate/', views.allocate, name='allocate'),
    path('transfer/<int:student_pk>/', views.transfer, name='transfer'),
    path('vacate/<int:allocation_pk>/', views.vacate, name='vacate'),
    path('waitlist/', views.waitlist, name='waitlist'),
    path('waitlist/add/', views.waitlist_add, name='waitlist_add'),
    path('waitlist/<int:pk>/remove/', views.waitlist_remove, name='waitlist_remove'),
    path('rules/', views.rules, name='rules'),
    path('report/', views.report, name='report'),
    path('my-room/', views.my_room, name='my_room'),
]
