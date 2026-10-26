from django.urls import path
from . import views

app_name = 'hostel'

urlpatterns = [
    path('', views.index, name='index'),
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),

    # AJAX
    path('ajax/floors/', views.ajax_floors, name='ajax_floors'),
    path('ajax/rooms/', views.ajax_rooms, name='ajax_rooms'),
    path('ajax/beds/', views.ajax_beds, name='ajax_beds'),

    # CRUD
    path('buildings/create/', views.building_create, name='building_create'),
    path('buildings/<int:pk>/delete/', views.building_delete, name='building_delete'),
    path('floors/create/', views.floor_create, name='floor_create'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),
    path('beds/<int:pk>/toggle-maintenance/', views.bed_toggle_maintenance, name='bed_toggle'),
]
