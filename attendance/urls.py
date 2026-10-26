from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.index, name='index'),
    path('bulk-save/', views.bulk_save, name='bulk_save'),
    path('student/<int:student_pk>/', views.student_attendance, name='student'),
]
