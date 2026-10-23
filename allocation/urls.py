from django.urls import path

from . import views

app_name = 'allocation'

urlpatterns = [
    path('my-room/', views.my_room, name='my_room'),
]
