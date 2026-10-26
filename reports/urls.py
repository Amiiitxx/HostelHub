from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('occupancy/', views.occupancy_report, name='occupancy_report'),
    path('students/', views.student_report, name='student_report'),
    path('fees/', views.fee_report, name='fee_report'),
    path('complaints/', views.complaint_report, name='complaint_report'),
    path('visitors/', views.visitor_report, name='visitor_report'),
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('allocations/', views.allocation_report, name='allocation_report'),
]
