from django.urls import path

from . import views

app_name = 'leave'

urlpatterns = [
    # Student endpoints
    path('my-leaves/', views.my_leaves, name='my_leaves'),
    path('apply/', views.apply_leave, name='apply'),
    path('<int:pk>/resubmit/', views.resubmit_leave, name='resubmit'),
    path('<int:pk>/cancel/', views.cancel_leave, name='cancel'),

    # Staff endpoints (Warden / Admin)
    path('review/', views.review_list, name='review'),
    path('review/<int:pk>/', views.review_detail, name='review_detail'),
    path('records/', views.consolidated_records, name='records'),
]
