from django.urls import path
from . import views

app_name = 'allocations'

urlpatterns = [
    path('', views.allocation_list, name='list'),
    path('create/', views.allocation_create, name='create'),
    path('<int:pk>/', views.allocation_detail, name='detail'),
    path('<int:pk>/vacate/', views.allocation_vacate, name='vacate'),
]
