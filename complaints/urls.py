from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.complaint_list, name='list'),
    path('create/', views.complaint_create, name='create'),
    path('<int:pk>/', views.complaint_detail, name='detail'),
    path('<int:pk>/update/', views.complaint_update, name='update'),
    path('<int:pk>/delete/', views.complaint_delete, name='delete'),
]
